from collections.abc import AsyncIterator

import httpx
import pytest

from app.main import app
from app.rag.store import KnowledgeBase

FRONT = "---\ntitle: Sample\ncategory: demo\nlast_updated: 2026-09-01\n---\n"
DOC = FRONT + "## A\n\nOne.\n\n## B\n\nTwo.\n"


@pytest.fixture
async def client(
    kb: KnowledgeBase, session_factory, admin_auth: dict[str, str]
) -> AsyncIterator[httpx.AsyncClient]:
    app.state.kb = kb
    app.state.session_factory = session_factory
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers=admin_auth
    ) as http:
        yield http
    app.state.kb = None
    app.state.session_factory = None


def upload(name: str, content: str | bytes) -> dict:
    return {"files": {"file": (name, content, "text/markdown")}}


async def test_upload_ingests_and_lists_the_document(client: httpx.AsyncClient) -> None:
    response = await client.post("/documents", **upload("sample.md", DOC))
    assert response.status_code == 200
    assert response.json() == {"source": "sample.md", "chunks": 2}

    listed = await client.get("/documents")
    assert listed.json() == [{"source": "sample.md", "chunks": 2}]


async def test_uploaded_document_is_searchable_without_restart(
    client: httpx.AsyncClient, kb: KnowledgeBase
) -> None:
    await client.post(
        "/documents",
        **upload("pizza.md", FRONT + "## Toppings\n\nPineapple pizza is allowed.\n"),
    )
    found = await kb.search("pineapple pizza", k=1)
    assert found[0][0].metadata["source"] == "pizza.md"


async def test_uploading_the_same_file_again_does_not_duplicate_it(
    client: httpx.AsyncClient,
) -> None:
    await client.post("/documents", **upload("sample.md", DOC))
    await client.post("/documents", **upload("sample.md", DOC))
    assert (await client.get("/documents")).json() == [{"source": "sample.md", "chunks": 2}]


async def test_delete_removes_the_document_then_404s(client: httpx.AsyncClient) -> None:
    await client.post("/documents", **upload("sample.md", DOC))

    assert (await client.delete("/documents/sample.md")).status_code == 204
    assert (await client.get("/documents")).json() == []

    again = await client.delete("/documents/sample.md")
    assert again.status_code == 404
    assert again.json()["code"] == "document_not_found"


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("sample.md", "no front matter"),
        ("sample.md", "---\ntitle: T\n---\nbody"),
        ("sample.pdf", DOC),
        ("sample.md", b"\xff\xfe\x00 not utf-8"),
    ],
)
async def test_invalid_uploads_are_rejected_and_store_nothing(
    client: httpx.AsyncClient, name: str, content: str | bytes
) -> None:
    response = await client.post("/documents", **upload(name, content))
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_document"
    assert (await client.get("/documents")).json() == []


async def test_oversized_upload_is_rejected(client: httpx.AsyncClient) -> None:
    response = await client.post("/documents", **upload("big.md", FRONT + "x" * 250_000))
    assert response.status_code == 413
    assert response.json()["code"] == "document_too_large"


async def test_documents_are_unavailable_when_no_knowledge_base_is_configured(
    client: httpx.AsyncClient,
) -> None:
    app.state.kb = None
    response = await client.get("/documents")
    assert response.status_code == 503
    assert response.json()["code"] == "knowledge_base_unavailable"
