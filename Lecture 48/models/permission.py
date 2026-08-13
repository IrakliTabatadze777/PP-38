from enum import Enum

from sqlalchemy import String, ForeignKey, UniqueConstraint, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.user import UserRole


class PermissionCode(str, Enum):
    PRODUCTS_CREATE = 'products:create'
    PRODUCTS_UPDATE = 'products:update'
    PRODUCTS_DELETE = 'products:delete'
    ORDERS_READ = 'orders:read'
    ORDERS_CREATE = 'orders:create'
    ORDERS_UPDATE = 'orders:update'
    ORDERS_DELETE = 'orders:delete'
    USERS_READ = 'users:read'
    USERS_CREATE = 'users:create'
    USERS_UPDATE = 'users:update'
    USERS_DELETE = 'users:delete'


class Permission(Base):
    __tablename__ = 'permissions'

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role_permissions: Mapped[list['RolePermission']] = relationship(
        back_populates='permission',
        cascade='all, delete-orphan',
    )


class RolePermission(Base):
    __tablename__ = 'role_permissions'
    __table_args__ = (
        UniqueConstraint('role', 'permission_id', name='uq_role_permission'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=lambda enum: [item.name for item in enum]),
        nullable=False,
    )
    permission_id: Mapped[int] = mapped_column(ForeignKey('permissions.id'), nullable=False)

    permission: Mapped[Permission] = relationship(back_populates='role_permissions')
