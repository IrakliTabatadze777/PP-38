from typing import TypedDict

from app.rag.store import KnowledgeBase


class Passage(TypedDict):
    source: str
    section: str
    text: str
    score: float


async def retrieve(kb: KnowledgeBase, query: str, *, top_k: int, min_score: float) -> list[Passage]:
    found = await kb.search(query, k=top_k)
    return [
        Passage(
            source=doc.metadata["source"],
            section=doc.metadata["section"],
            text=doc.page_content,
            score=round(score, 4),
        )
        for doc, score in found
        if score >= min_score
    ]
