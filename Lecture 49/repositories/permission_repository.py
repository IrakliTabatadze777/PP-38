from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.permission import Permission, RolePermission
from models.user import UserRole


class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_codes_for_role(self, role: UserRole) -> set[str]:
        stmt = (
            select(RolePermission)
            .where(RolePermission.role == role)
            .options(selectinload(RolePermission.permission))
        )
        result = await self.db.scalars(stmt)
        role_permissions = result.all()
        return {rp.permission.code for rp in role_permissions}

    async def role_has_permission(self, role: UserRole, permission_code: str) -> bool:
        stmt = (
            select(RolePermission.id)
            .join(Permission)
            .where(
                RolePermission.role == role,
                Permission.code == permission_code,
            )
            .limit(1)
        )
        result = await self.db.scalar(stmt)
        return result is not None
