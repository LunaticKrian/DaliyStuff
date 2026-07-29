"""首启 seed：确保超级管理员账号存在。

明文口令只取自 settings（.env 可覆盖）；入库即 bcrypt 哈希，仓库里不存明文。
账号标记 must_change_password=True，首登强制改密。
"""
import logging

from app.config import settings
from app.database import async_session_factory
from app.models.user import User
from app.services.auth import get_user_by_username
from app.utils.security import get_password_hash

logger = logging.getLogger(__name__)


async def ensure_superadmin() -> None:
    """若 SUPERADMIN_USERNAME 对应用户不存在则创建（is_admin=True）。已存在则不动。"""
    async with async_session_factory() as db:
        existing = await get_user_by_username(db, settings.SUPERADMIN_USERNAME)
        if existing is not None:
            return
        user = User(
            username=settings.SUPERADMIN_USERNAME,
            password_hash=get_password_hash(settings.SUPERADMIN_PASSWORD),
            is_admin=True,
            must_change_password=True,
            profile_completed=True,  # 跳过角色建档引导，避免后台被强制跳走
        )
        db.add(user)
        await db.commit()
        logger.warning(
            "[seed] 已创建超级管理员 '%s'（口令来自 SUPERADMIN_PASSWORD，请首登后立即修改）",
            settings.SUPERADMIN_USERNAME,
        )
