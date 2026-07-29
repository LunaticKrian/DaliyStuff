from sqlalchemy import Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserQuota(Base):
    """每用户月度配额（由管理员设置；NULL 表示不限）。"""

    __tablename__ = "user_quotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    monthly_token_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monthly_cost_cap_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
