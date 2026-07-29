from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IntelArticle(Base):
    """AI 技术情报文章。

    v260729 起改 per-user：每条归属生成它的用户（user_id）。历史数据 user_id 为空，
    视为公共数据（前端默认仅展示当前用户的）。
    对齐前端 web/src/types/intel.ts 的 Article 接口。
    published_at = 推送日（生成当天），非原文真实发布日。
    """

    __tablename__ = "intel_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    region: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    source: Mapped[str] = mapped_column(String(200), nullable=False, default="", server_default="")
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    read_time: Mapped[str] = mapped_column(String(16), nullable=False, default="5 min", server_default="5 min")
    published_at: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
