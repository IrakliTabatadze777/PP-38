from app.config.settings import settings
from app.rag.retriever import Passage, retrieve
from app.rag.store import KnowledgeBase
from app.schemas.tools import SearchKnowledgeBaseInput


async def search_knowledge_base(
    kb: KnowledgeBase, args: SearchKnowledgeBaseInput, *, min_score: float | None = None
) -> list[Passage]:
    if min_score is None:
        min_score = settings.retrieval_min_score
    return await retrieve(kb, args.query, top_k=args.top_k, min_score=min_score)
