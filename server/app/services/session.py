"""Refresh 会话服务：建会话、轮换、复用吊销、设备列表/踢出。

状态机要点：
- 一次登录 = 一行 RefreshSession（family_id 唯一）；`current_jti` 为当前有效 refresh 的 jti。
- `rotate_session` 换新 jti 并滑动续期（活跃用户不掉线）；旧 jti 随即失效。
- 复用检测：refresh 提交的 jti ≠ current_jti → 视为旧/被盗 token 重放 → 仅吊销本会话（会话级，不连坐其他设备）。
- `sid`（= 会话 id）在 access/refresh 中稳定；access 校验仅靠 sid，复用检测靠 jti。
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.session import RefreshSession
from app.utils.security import create_access_token, create_refresh_token


def _new_jti() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    # SQLite 经 SQLAlchemy 回读 DateTime 不带 tzinfo；统一用 naive UTC 比较，避免 aware/naive 冲突。
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def create_session(
    db: AsyncSession,
    user_id: int,
    device_name: str | None = None,
    device_platform: str | None = None,
) -> RefreshSession:
    now = _now()
    session = RefreshSession(
        user_id=user_id,
        family_id=uuid.uuid4().hex,
        current_jti=_new_jti(),
        device_name=device_name,
        device_platform=device_platform,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(session)
    await db.flush()
    return session


def build_tokens_for_session(session: RefreshSession) -> dict[str, str]:
    token_data = {"sub": str(session.user_id)}
    return {
        "access_token": create_access_token(token_data, sid=session.id),
        "refresh_token": create_refresh_token(token_data, sid=session.id, jti=session.current_jti),
        "token_type": "bearer",
    }


async def get_session(db: AsyncSession, session_id: int) -> RefreshSession | None:
    result = await db.execute(select(RefreshSession).where(RefreshSession.id == session_id))
    return result.scalar_one_or_none()


def is_active(session: RefreshSession) -> bool:
    return (not session.revoked) and session.expires_at > _now()


async def rotate_session(db: AsyncSession, session: RefreshSession) -> dict[str, str]:
    """轮换：新 jti + 滑动续期。返回新 access/refresh token 对。"""
    now = _now()
    session.current_jti = _new_jti()
    session.last_seen_at = now
    session.expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(session)
    await db.flush()
    return build_tokens_for_session(session)


async def revoke_session(db: AsyncSession, session: RefreshSession) -> None:
    session.revoked = True
    db.add(session)
    await db.flush()


async def revoke_other_sessions(
    db: AsyncSession, user_id: int, except_session_id: int
) -> None:
    await db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.id != except_session_id,
            RefreshSession.revoked == False,  # noqa: E712
        )
        .values(revoked=True)
    )


async def list_sessions(db: AsyncSession, user_id: int) -> list[RefreshSession]:
    result = await db.execute(
        select(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked == False,  # noqa: E712
            RefreshSession.expires_at > _now(),
        )
        .order_by(RefreshSession.last_seen_at.desc())
    )
    return list(result.scalars().all())
