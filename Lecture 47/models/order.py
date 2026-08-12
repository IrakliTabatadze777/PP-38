from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float, ForeignKey
from core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)