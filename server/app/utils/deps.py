from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.session import RefreshSession
from app.models.user import User
from app.services.auth import get_user_by_id
from app.services.session import get_session, is_active
from app.utils.security import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_session(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> RefreshSession:
    """解码 access token 并校验其会话仍存活（吊销/过期立即生效）。"""
    credentials_exception = _credentials_exception()
    try:
        payload = verify_token(token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    sid = payload.get("sid")
    if user_id is None or sid is None:
        raise credentials_exception

    session = await get_session(db, int(sid))
    if session is None or not is_active(session):
        raise credentials_exception

    return session


async def get_current_user(
    session: RefreshSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = _credentials_exception()
    user = await get_user_by_id(db, session.user_id)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用",
        )
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """要求当前用户是管理员（is_admin）。用于 /api/admin/* 路由。"""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限",
        )
    return user
