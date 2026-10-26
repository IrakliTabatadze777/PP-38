import re
from pathlib import Path

import pytest

from app.config import policy
from app.rag.ingest import (
    CHUNK_SIZE,
    InvalidDocument,
    chunk_document,
    chunk_id,
    parse_front_matter,
    read_documents,
    validate_source_name,
)

KB_DIR = Path(__file__).resolve().parents[2] / "data" / "kb"
EXPECTED_FILES = {
    "returns_policy.md",
    "refund_policy.md",
    "damaged_or_defective.md",
    "final_sale_items.md",
    "shipping_policy.md",
    "warranty.md",
    "product_care_faq.md",
    "order_status_faq.md",
    "contact_and_escalation.md",
}

DOC = """---
title: Sample
category: demo
last_updated: 2026-09-01
---

Intro text before any heading.

## First topic

Alpha beta gamma.

## Second topic

Delta epsilon.

### Detail

Zeta eta theta.
"""


@pytest.fixture(scope="module")
def kb_documents() -> dict[str, str]:
    return read_documents(KB_DIR)


class TestFrontMatter:
    def test_reads_the_fields_and_returns_the_body(self) -> None:
        front, body = parse_front_matter(DOC)
        assert front == {"title": "Sample", "category": "demo", "last_updated": "2026-09-01"}
        assert body.lstrip().startswith("Intro text")

    @pytest.mark.parametrize(
        "text",
        [
            "No front matter at all",
            "---\ntitle: Only a title\n---\nbody",
            "---\n- just\n- a list\n---\nbody",
            "---\ntitle: [unclosed\n---\nbody",
        ],
    )
    def test_rejects_bad_front_matter(self, text: str) -> None:
        with pytest.raises(InvalidDocument):
            parse_front_matter(text)


class TestChunking:
    def test_metadata_has_source_section_category_and_date(self) -> None:
        chunks = chunk_document("sample.md", DOC)
        assert {c.metadata["source"] for c in chunks} == {"sample.md"}
        assert {c.metadata["category"] for c in chunks} == {"demo"}
        assert {c.metadata["last_updated"] for c in chunks} == {"2026-09-01"}

    def test_section_is_the_nearest_heading(self) -> None:
        sections = [c.metadata["section"] for c in chunk_document("sample.md", DOC)]
        assert sections == ["Sample", "First topic", "Second topic", "Detail"]

    def test_chunk_text_starts_with_its_section(self) -> None:
        for chunk in chunk_document("sample.md", DOC):
            assert chunk.text.startswith(chunk.metadata["section"] + "\n")

    def test_long_sections_are_split_by_size(self) -> None:
        body = " ".join(f"word{i}" for i in range(400))
        text = DOC.split("## First")[0] + f"## Long\n\n{body}\n"
        chunks = chunk_document("long.md", text)
        long_chunks = [c for c in chunks if c.metadata["section"] == "Long"]
        assert len(long_chunks) > 1
        assert all(len(c.text) <= CHUNK_SIZE + len("Long\n") for c in long_chunks)

    def test_ids_are_deterministic_and_unique(self) -> None:
        first = [c.id for c in chunk_document("sample.md", DOC)]
        again = [c.id for c in chunk_document("sample.md", DOC)]
        other_source = [c.id for c in chunk_document("other.md", DOC)]
        assert first == again
        assert len(set(first)) == len(first)
        assert not set(first) & set(other_source)
        assert first[0] == chunk_id("sample.md", 0)

    def test_document_without_content_is_rejected(self) -> None:
        with pytest.raises(InvalidDocument):
            chunk_document(
                "empty.md", "---\ntitle: T\ncategory: c\nlast_updated: 2026-01-01\n---\n"
            )


class TestSourceName:
    @pytest.mark.parametrize("name", ["a.md", "returns_policy.md", "notes-2.txt"])
    def test_accepts_plain_names(self, name: str) -> None:
        validate_source_name(name)

    @pytest.mark.parametrize(
        "name", ["", "a.pdf", "../a.md", "dir/a.md", "a b.md", ".hidden.md", "a.md.exe"]
    )
    def test_rejects_other_names(self, name: str) -> None:
        with pytest.raises(InvalidDocument):
            validate_source_name(name)


class TestKnowledgeBaseFiles:
    def test_the_nine_documents_exist(self, kb_documents: dict[str, str]) -> None:
        assert set(kb_documents) == EXPECTED_FILES

    def test_every_document_is_200_to_600_words(self, kb_documents: dict[str, str]) -> None:
        for name, text in kb_documents.items():
            assert 200 <= len(text.split()) <= 600, name

    def test_chunks_never_mix_sections(self, kb_documents: dict[str, str]) -> None:
        for name, text in kb_documents.items():
            headings = re.findall(r"^#{2,3} (.+)$", text, flags=re.MULTILINE)
            for chunk in chunk_document(name, text):
                own = chunk.metadata["section"]
                assert chunk.text.startswith(own + "\n"), name
                for heading in headings:
                    if heading != own:
                        assert heading not in chunk.text, (name, own, heading)

    def test_chunks_fit_the_size_target(self, kb_documents: dict[str, str]) -> None:
        for name, text in kb_documents.items():
            for chunk in chunk_document(name, text):
                assert len(chunk.text) <= CHUNK_SIZE + len(chunk.metadata["section"]) + 1, name


class TestDocumentsMatchPolicy:
    def test_return_window_and_grace_period(self, kb_documents: dict[str, str]) -> None:
        returns = kb_documents["returns_policy.md"]
        assert f"within {policy.RETURN_WINDOW_DAYS} days" in returns
        grace_start = policy.RETURN_WINDOW_DAYS + 1
        assert f"{grace_start} to {policy.GRACE_PERIOD_END_DAYS} days" in returns
        assert f"After {policy.GRACE_PERIOD_END_DAYS} days" in returns

    def test_damaged_items_use_the_same_windows(self, kb_documents: dict[str, str]) -> None:
        damaged = kb_documents["damaged_or_defective.md"]
        assert f"{policy.RETURN_WINDOW_DAYS} days ago or less" in damaged
        grace_start = policy.RETURN_WINDOW_DAYS + 1
        assert f"{grace_start} to {policy.GRACE_PERIOD_END_DAYS} days ago" in damaged
        assert f"{policy.GRACE_PERIOD_END_DAYS} days" in damaged

    def test_warranty_years_per_category(self, kb_documents: dict[str, str]) -> None:
        warranty = kb_documents["warranty.md"].lower()
        for years in set(policy.WARRANTY_YEARS.values()):
            categories = [c for c, y in policy.WARRANTY_YEARS.items() if y == years]
            sentence = f"{' and '.join(categories)} are covered for {years} year"
            assert sentence in warranty, sentence

    def test_refund_timing_method_and_high_value_threshold(
        self, kb_documents: dict[str, str]
    ) -> None:
        refunds = kb_documents["refund_policy.md"]
        low, high = policy.REFUND_TIMING_BUSINESS_DAYS
        assert f"{low} to {high} business days" in refunds
        assert policy.REFUND_METHOD in refunds
        assert f"over {policy.HIGH_VALUE_THRESHOLD_CENTS // 100} USD" in refunds
