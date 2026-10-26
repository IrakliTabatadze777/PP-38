from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, UploadFile

from app.api.auth import AdminOnly
from app.api.errors import ApiError
from app.rag.store import KnowledgeBase
from app.schemas.documents import DocumentInfo
from app.services import documents as service

router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[AdminOnly])


def get_knowledge_base(request: Request) -> KnowledgeBase:
    kb: KnowledgeBase | None = getattr(request.app.state, "kb", None)
    if kb is None:
        raise ApiError(503, "knowledge_base_unavailable", "The knowledge base is not configured")
    return kb


KnowledgeBaseDep = Annotated[KnowledgeBase, Depends(get_knowledge_base)]


@router.post("")
async def upload_document(file: UploadFile, kb: KnowledgeBaseDep) -> DocumentInfo:
    data = await file.read(service.MAX_UPLOAD_BYTES + 1)
    return await service.upload_document(kb, file.filename or "", data)


@router.get("")
async def list_documents(kb: KnowledgeBaseDep) -> list[DocumentInfo]:
    return await service.list_documents(kb)


@router.delete("/{source}", status_code=204)
async def delete_document(source: str, kb: KnowledgeBaseDep) -> Response:
    await service.delete_document(kb, source)
    return Response(status_code=204)
