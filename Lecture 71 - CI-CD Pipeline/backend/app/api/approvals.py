from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.auth import ReviewerOnly, ReviewerUser
from app.api.chat import GraphDep
from app.api.deps import SessionFactoryDep
from app.schemas.approvals import (
    ApprovalDetail,
    ApprovalStatus,
    ApprovalSummary,
    DecisionRequest,
    DecisionResponse,
)
from app.services import approvals as service

router = APIRouter(prefix="/approvals", tags=["approvals"], dependencies=[ReviewerOnly])

ApprovalId = Annotated[str, Path(max_length=40)]


@router.get("")
async def list_approvals(
    factory: SessionFactoryDep,
    status: ApprovalStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ApprovalSummary]:
    return await service.list_approvals(factory, status, limit)


@router.get("/{approval_id}")
async def get_approval(approval_id: ApprovalId, factory: SessionFactoryDep) -> ApprovalDetail:
    return await service.get_approval(factory, approval_id)


@router.post("/{approval_id}/decision")
async def decide(
    approval_id: ApprovalId,
    body: DecisionRequest,
    graph: GraphDep,
    factory: SessionFactoryDep,
    reviewer: ReviewerUser,
) -> DecisionResponse:
    return await service.decide(graph, factory, reviewer, approval_id, body)
