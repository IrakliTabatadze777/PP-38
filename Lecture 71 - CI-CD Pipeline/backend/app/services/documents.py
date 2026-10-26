from app.rag.ingest import InvalidDocument, ingest_document, validate_source_name
from app.rag.store import KnowledgeBase
from app.schemas.documents import DocumentInfo
from app.services.errors import InvalidInput, NotFound, TooLarge

MAX_UPLOAD_BYTES = 200_000


async def upload_document(kb: KnowledgeBase, source: str, data: bytes) -> DocumentInfo:
    if len(data) > MAX_UPLOAD_BYTES:
        raise TooLarge("document_too_large", "The file is larger than 200 KB")
    try:
        validate_source_name(source)
        text = data.decode("utf-8")
        chunks = await ingest_document(kb, source, text)
    except UnicodeDecodeError:
        raise InvalidInput("invalid_document", "The file must be UTF-8 text") from None
    except InvalidDocument as exc:
        raise InvalidInput("invalid_document", str(exc)) from None
    return DocumentInfo(source=source, chunks=chunks)


async def list_documents(kb: KnowledgeBase) -> list[DocumentInfo]:
    return [DocumentInfo(source=s, chunks=n) for s, n in (await kb.list_sources()).items()]


async def delete_document(kb: KnowledgeBase, source: str) -> None:
    if not await kb.delete_source(source):
        raise NotFound("document_not_found", "No such document")
