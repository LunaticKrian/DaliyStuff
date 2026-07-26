"""冒险者履历 DOSSIER 数据模型。

一份简历 Resume 的内容存于 ResumeSnapshot.data（JSON），每次接受变更 / 手动保存
即追加一条快照（revision 单调递增），历史不可变 → Undo = 指向某快照再追加。

AI 产出的变更不直接落库，先写 PendingChange（status=pending），用户确认后回放。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), default="我的简历", nullable=False)
    lang: Mapped[str] = mapped_column(String(8), default="zh", nullable=False)  # zh | en（当前显示+编辑语言）
    template: Mapped[str] = mapped_column(String(32), default="pixel", nullable=False)  # pixel | pro | minimal | academic
    current_revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False,
    )


class ResumeSnapshot(Base):
    """每次落库追加一条；data 存完整简历 JSON。回滚 = 把某 snapshot 作为新 revision 追加。"""

    __tablename__ = "resume_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    summary: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="manual", nullable=False)  # manual | nexa
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class ResumeChatThread(Base):
    __tablename__ = "resume_chat_threads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class ResumeChatMessage(Base):
    __tablename__ = "resume_chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("resume_chat_threads.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class PendingChange(Base):
    """AI 产出、待用户确认的变更。接受/拒绝后置 status；接受时按 args 在当前数据上回放。"""

    __tablename__ = "resume_pending_changes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False)
    thread_id: Mapped[int] = mapped_column(ForeignKey("resume_chat_threads.id", ondelete="CASCADE"), index=True, nullable=False)
    group_id: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    tool: Mapped[str] = mapped_column(String(40), nullable=False)
    args: Mapped[dict] = mapped_column(JSON, nullable=False)
    diff: Mapped[dict] = mapped_column(JSON, nullable=False)
    base_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    lang: Mapped[str] = mapped_column(String(8), default="zh", nullable=False)  # 该变更针对的语言侧（zh | en）
    status: Mapped[str] = mapped_column(String(12), default="pending", nullable=False)  # pending | applied | denied
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
