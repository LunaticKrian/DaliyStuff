from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserAIConfig(Base):
    """单个用户的 AI 模型配置（一用户一行）。

    api_key_enc 为 Fernet 密文；任何接口都不回显明文，仅返回 mask_key 后的掩码。
    """

    __tablename__ = "user_ai_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, default="anthropic", server_default="anthropic",
    )
    model: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    base_url: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    api_key_enc: Mapped[str] = mapped_column(String(512), nullable=False, default="", server_default="")
    max_turns: Mapped[int] = mapped_column(Integer, nullable=False, default=12, server_default="12")
    max_budget_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.5, server_default="0.5")
    system_prompt_extra: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False,
    )
