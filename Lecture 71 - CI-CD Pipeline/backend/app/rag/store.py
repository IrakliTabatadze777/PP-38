from collections.abc import Sequence

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_postgres import PGVector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

COLLECTION = "kb"

_SOURCE_IDS = text(
    "SELECT e.id FROM langchain_pg_embedding e "
    "JOIN langchain_pg_collection c ON c.uuid = e.collection_id "
    "WHERE c.name = :collection AND e.cmetadata->>'source' = :source"
)
_SOURCE_COUNTS = text(
    "SELECT e.cmetadata->>'source' AS source, count(*) AS chunks "
    "FROM langchain_pg_embedding e "
    "JOIN langchain_pg_collection c ON c.uuid = e.collection_id "
    "WHERE c.name = :collection GROUP BY 1 ORDER BY 1"
)


class KnowledgeBase:
    def __init__(
        self, embeddings: Embeddings, database_url: str, *, collection: str = COLLECTION
    ) -> None:
        self.collection = collection
        self._engine: AsyncEngine = create_async_engine(database_url)
        self._store = PGVector(
            embeddings,
            connection=self._engine,
            collection_name=collection,
            async_mode=True,
            create_extension=False,
        )
        self._ready = False

    async def _setup(self) -> None:
        if not self._ready:
            await self._store.acreate_tables_if_not_exists()
            await self._store.acreate_collection()
            self._ready = True

    async def _source_ids(self, source: str) -> list[str]:
        async with self._engine.connect() as conn:
            params = {"collection": self.collection, "source": source}
            result = await conn.execute(_SOURCE_IDS, params)
            return [row.id for row in result]

    async def replace_source(
        self, source: str, documents: Sequence[Document], ids: Sequence[str]
    ) -> None:
        await self._setup()
        await self._store.aadd_documents(list(documents), ids=list(ids))
        stale = set(await self._source_ids(source)) - set(ids)
        if stale:
            await self._store.adelete(ids=sorted(stale))

    async def delete_source(self, source: str) -> int:
        await self._setup()
        ids = await self._source_ids(source)
        if ids:
            await self._store.adelete(ids=ids)
        return len(ids)

    async def list_sources(self) -> dict[str, int]:
        await self._setup()
        async with self._engine.connect() as conn:
            result = await conn.execute(_SOURCE_COUNTS, {"collection": self.collection})
            return {row.source: row.chunks for row in result}

    async def search(self, query: str, k: int) -> list[tuple[Document, float]]:
        await self._setup()
        found = await self._store.asimilarity_search_with_score(query, k=k)
        return [(doc, 1.0 - distance) for doc, distance in found]

    async def drop(self) -> None:
        await self._setup()
        await self._store.adelete_collection()
        self._ready = False

    async def aclose(self) -> None:
        await self._engine.dispose()
