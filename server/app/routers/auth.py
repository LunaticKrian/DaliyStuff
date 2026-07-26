from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.session import RefreshSession
from app.models.user import User
from app.schemas.auth import (
    PasswordChange,
    PortraitUploadResponse,
    ProfileUpdate,
    RefreshTokenRequest,
    SessionResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.services.auth import (
    authenticate_user,
    change_password,
    register_user,
    update_profile,
    update_user,
    upload_portrait,
)
from app.services.session import (
    build_tokens_for_session,
    create_session,
    get_session,
    is_active,
    list_sessions,
    revoke_other_sessions,
    revoke_session,
    rotate_session,
)
from app.utils.deps import get_current_session, get_current_user
from app.utils.security import verify_token

router = APIRouter(prefix="/api/auth")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    x_device_name: str | None = Header(default=None),
    x_device_platform: str | None = Header(default=None),
) -> TokenResponse:
    user = await register_user(db, user_data)
    session = await create_session(db, user.id, x_device_name, x_device_platform)
    return TokenResponse(**build_tokens_for_session(session))


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
    x_device_name: str | None = Header(default=None),
    x_device_platform: str | None = Header(default=None),
) -> TokenResponse:
    user = await authenticate_user(db, credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    session = await create_session(db, user.id, x_device_name, x_device_platform)
    return TokenResponse(**build_tokens_for_session(session))


@router.post("/logout")
async def logout(
    session: RefreshSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    # 真实登出：吊销当前会话（access/refresh 同时失效）。
    await revoke_session(db, session)
    return {"message": "logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        payload = verify_token(body.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    sid = payload.get("sid")
    jti = payload.get("jti")
    user_id = payload.get("sub")
    if sid is None or jti is None or user_id is None:
        # 旧版无状态令牌（无 sid/jti）→ 一次性拒绝，引导重登。
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    session = await get_session(db, int(sid))
    if session is None or not is_active(session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # 复用检测：提交的 jti 不是当前 jti → 旧/被盗 token 重放 → 吊销本会话族。
    if session.current_jti != jti:
        await revoke_session(db, session)
        await db.commit()  # 复用吊销须在抛 401 前落库（get_db 在异常分支会回滚）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected",
        )

    # 轮换：新 jti + 滑动续期。
    return TokenResponse(**await rotate_session(db, session))


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await update_user(db, current_user, update_data)


@router.put("/password")
async def update_password(
    body: PasswordChange,
    session: RefreshSession = Depends(get_current_session),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    success = await change_password(db, current_user, body.old_password, body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    # 改密码：踢其他设备、保留本机会话。
    await revoke_other_sessions(db, current_user.id, except_session_id=session.id)
    return {"message": "password changed"}


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await update_profile(db, current_user, data)


@router.post("/portrait", response_model=PortraitUploadResponse)
async def upload_user_portrait(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortraitUploadResponse:
    url = await upload_portrait(db, current_user, file)
    return PortraitUploadResponse(url=url)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_user_sessions(
    current_session: RefreshSession = Depends(get_current_session),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SessionResponse]:
    sessions = await list_sessions(db, current_user.id)
    return [
        SessionResponse(
            id=s.id,
            device_name=s.device_name,
            device_platform=s.device_platform,
            created_at=s.created_at,
            last_seen_at=s.last_seen_at,
            is_current=(s.id == current_session.id),
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
async def revoke_user_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    target = await get_session(db, session_id)
    if target is None or target.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    await revoke_session(db, target)
    return {"message": "session revoked"}
