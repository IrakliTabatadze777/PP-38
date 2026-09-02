from sqlalchemy.ext.asyncio import AsyncSession

from models.user import UserRole
from repositories.permission_repository import PermissionRepository


class PermissionService:
    def __init__(self, db: AsyncSession):
        self.repository = PermissionRepository(db)

    async def get_codes_for_role(self, role: UserRole) -> set[str]:
        return await self.repository.get_codes_for_role(role)

    async def user_has_permission(self, role: UserRole, permission_code: str) -> bool:
        return await self.repository.role_has_permission(role, permission_code)
