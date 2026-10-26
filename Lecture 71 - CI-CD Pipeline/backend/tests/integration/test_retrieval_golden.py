import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import yaml

from app.config.settings import settings
from app.rag.embeddings import EmbeddingsNotConfigured, make_embeddings
from app.rag.ingest import ingest_directory
from app.rag.retriever import retrieve
from app.rag.store import KnowledgeBase

pytestmark = pytest.mark.slow

KB_DIR = Path(__file__).resolve().parents[2] / "data" / "kb"
GOLDEN = yaml.safe_load((Path(__file__).resolve().parents[1] / "golden_questions.yaml").read_text())
TARGET = 0.9
TOP_K = 4


@pytest.fixture
async def real_kb(migrated_test_db: str) -> AsyncIterator[KnowledgeBase]:
    try:
        embeddings = make_embeddings()
    except EmbeddingsNotConfigured as exc:
        pytest.skip(str(exc))
    knowledge_base = KnowledgeBase(
        embeddings, migrated_test_db, collection=f"kb_golden_{uuid.uuid4().hex[:8]}"
    )
    await ingest_directory(knowledge_base, KB_DIR)
    yield knowledge_base
    await knowledge_base.drop()
    await knowledge_base.aclose()


async def test_expected_source_is_in_the_top_results(real_kb: KnowledgeBase) -> None:
    misses = []
    for item in GOLDEN["questions"]:
        found = await retrieve(real_kb, item["question"], top_k=TOP_K, min_score=0.0)
        if not {p["source"] for p in found} & set(item["sources"]):
            misses.append(item["question"])

    hit_rate = 1 - len(misses) / len(GOLDEN["questions"])
    assert hit_rate >= TARGET, f"hit rate {hit_rate:.0%}; missed: {misses}"


async def test_threshold_separates_answerable_from_out_of_scope_questions(
    real_kb: KnowledgeBase,
) -> None:
    threshold = settings.retrieval_min_score

    async def best_score(question: str) -> float:
        found = await retrieve(real_kb, question, top_k=1, min_score=0.0)
        return found[0]["score"] if found else 0.0

    answerable = {q["question"]: await best_score(q["question"]) for q in GOLDEN["questions"]}
    out_of_scope = {q: await best_score(q) for q in GOLDEN["out_of_scope"]}
    print(f"\nanswerable: lowest {min(answerable.values())}")
    print(f"out of scope: highest {max(out_of_scope.values())}")
    print(f"threshold: {threshold}")

    too_strict = [q for q, s in answerable.items() if s < threshold]
    too_loose = [q for q, s in out_of_scope.items() if s >= threshold]
    assert not too_strict, f"relevant questions below the threshold: {too_strict}"
    assert not too_loose, f"out-of-scope questions above the threshold: {too_loose}"
