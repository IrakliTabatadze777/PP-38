
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.database import get_db
from core.dependencies import require_permission
from models import User
from models.permission import PermissionCode
from schemas import CreateOrderRequest, CreateOrderResponse
from services import OrderService
from core.ws_manager import ws_manager

router = APIRouter(prefix='/orders', tags=['Orders'])


@router.get('/')
async def get_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.ORDERS_READ)),
):
    return {'message': 'get_orders'}


@router.get('/{order_id}')
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.ORDERS_READ)),
):
    return {'message': 'get_order', 'order_id': order_id}


@router.post('/', response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.ORDERS_CREATE)),
):
    order_service = OrderService(db)

    data_dict = {'total': data.total, 'user_id': current_user.id}
    response = await order_service.create_order(data_dict)

    await ws_manager.broadcast(
        {
            'type': 'order:create',
            'id': response.id,
            'user_id': response.user_id,
            'total': response.total,
        }
    )

    # return {'message': 'create_order', 'user_id': current_user.id}

    return response

@router.websocket('/ws')
async def order_websocket(socket: WebSocket):
    await ws_manager.connect(socket)

    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(socket)


@router.delete('/{order_id}')
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.ORDERS_DELETE)),
):
    return {'message': 'delete_order'}
