from pathlib import Path

import pytest

from app.rag.ingest import InvalidDocument, chunk_document, ingest_directory, ingest_document
from app.rag.retriever import retrieve
from app.rag.store import KnowledgeBase
from app.schemas.tools import SearchKnowledgeBaseInput
from app.tools.knowledge import search_knowledge_base

KB_DIR = Path(__file__).resolve().parents[2] / "data" / "kb"
FRONT = "---\ntitle: Sample\ncategory: demo\nlast_updated: 2026-09-01\n---\n"


class TestIngestion:
    async def test_chunks_are_stored_per_source(self, loaded_kb: KnowledgeBase) -> None:
        stored = await loaded_kb.list_sources()
        expected = {
            path.name: len(chunk_document(path.name, path.read_text("utf-8")))
            for path in KB_DIR.glob("*.md")
        }
        assert stored == expected
        assert len(stored) == 9

    async def test_reingesting_leaves_chunk_counts_unchanged(
        self, loaded_kb: KnowledgeBase
    ) -> None:
        before = await loaded_kb.list_sources()
        again = await ingest_directory(loaded_kb, KB_DIR)
        assert await loaded_kb.list_sources() == before
        assert again == before

    async def test_reingesting_one_file_twice_does_not_duplicate_it(
        self, kb: KnowledgeBase
    ) -> None:
        text = FRONT + "## A\n\nOne.\n\n## B\n\nTwo.\n"
        first = await ingest_document(kb, "doc.md", text)
        second = await ingest_document(kb, "doc.md", text)
        assert first == second == 2
        assert await kb.list_sources() == {"doc.md": 2}

    async def test_an_edited_file_replaces_its_chunks_and_drops_stale_ones(
        self, kb: KnowledgeBase
    ) -> None:
        await ingest_document(
            kb, "doc.md", FRONT + "## A\n\nalpha.\n\n## B\n\nbravo.\n\n## C\n\ncharlie.\n"
        )
        await ingest_document(kb, "doc.md", FRONT + "## A\n\nalpha changed.\n")

        assert await kb.list_sources() == {"doc.md": 1}
        found = await retrieve(kb, "alpha changed", top_k=4, min_score=0.0)
        assert [p["section"] for p in found] == ["A"]
        assert "changed" in found[0]["text"]

    async def test_invalid_documents_store_nothing(self, kb: KnowledgeBase) -> None:
        with pytest.raises(InvalidDocument):
            await ingest_document(kb, "bad.md", "no front matter")
        assert await kb.list_sources() == {}

    async def test_delete_source_removes_only_that_source(self, loaded_kb: KnowledgeBase) -> None:
        before = await loaded_kb.list_sources()
        removed = await loaded_kb.delete_source("warranty.md")
        after = await loaded_kb.list_sources()

        assert removed == before["warranty.md"]
        assert "warranty.md" not in after
        assert after == {k: v for k, v in before.items() if k != "warranty.md"}
        assert await loaded_kb.delete_source("warranty.md") == 0


class TestRetrieval:
    async def test_passages_carry_source_section_text_and_score(
        self, loaded_kb: KnowledgeBase
    ) -> None:
        found = await retrieve(loaded_kb, "warranty", top_k=4, min_score=0.0)

        assert 1 <= len(found) <= 4
        assert found[0]["source"] == "warranty.md"
        assert set(found[0]) == {"source", "section", "text", "score"}
        assert found[0]["text"].startswith(found[0]["section"])

    async def test_results_are_best_first(self, loaded_kb: KnowledgeBase) -> None:
        found = await retrieve(
            loaded_kb, "refund to my original payment method", top_k=4, min_score=0
        )
        scores = [p["score"] for p in found]
        assert scores == sorted(scores, reverse=True)

    async def test_top_k_limits_the_results(self, loaded_kb: KnowledgeBase) -> None:
        found = await retrieve(loaded_kb, "return refund shipping warranty", top_k=2, min_score=0)
        assert len(found) == 2

    async def test_nothing_relevant_gives_an_empty_list(self, loaded_kb: KnowledgeBase) -> None:
        found = await retrieve(
            loaded_kb, "quantum chromodynamics lagrangian", top_k=4, min_score=0.3
        )
        assert found == []

    async def test_threshold_filters_weak_matches(self, loaded_kb: KnowledgeBase) -> None:
        query = "wash my jacket"
        loose = await retrieve(loaded_kb, query, top_k=4, min_score=0.0)
        strict = await retrieve(loaded_kb, query, top_k=4, min_score=loose[0]["score"])
        assert len(strict) < len(loose)
        assert all(p["score"] >= loose[0]["score"] for p in strict)

    async def test_a_document_is_searchable_right_after_ingestion(self, kb: KnowledgeBase) -> None:
        assert await retrieve(kb, "pineapple pizza", top_k=4, min_score=0.3) == []
        await ingest_document(
            kb, "pizza.md", FRONT + "## Toppings\n\nPineapple pizza is allowed.\n"
        )
        found = await retrieve(kb, "pineapple pizza", top_k=4, min_score=0.3)
        assert [p["source"] for p in found] == ["pizza.md"]


class TestSearchTool:
    async def test_tool_returns_passages(self, loaded_kb: KnowledgeBase) -> None:
        args = SearchKnowledgeBaseInput(query="warranty")
        found = await search_knowledge_base(loaded_kb, args, min_score=0.1)
        assert found[0]["source"] == "warranty.md"

    async def test_tool_returns_empty_list_when_nothing_passes(
        self, loaded_kb: KnowledgeBase
    ) -> None:
        args = SearchKnowledgeBaseInput(query="warranty")
        assert await search_knowledge_base(loaded_kb, args, min_score=1.01) == []

    def test_top_k_defaults_to_four_and_is_bounded(self) -> None:
        assert SearchKnowledgeBaseInput(query="x").top_k == 4
        with pytest.raises(ValueError):
            SearchKnowledgeBaseInput(query="x", top_k=0)
        with pytest.raises(ValueError):
            SearchKnowledgeBaseInput(query="")
