import os
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.logging_config import setup_logging

# 必须在业务模块实例化 logger 之前完成配置
setup_logging()
from app.models import (  # noqa: F401 – ensure tables are created
    AdditionalCost,
    AuditLog,
    Category,
    ChatMessage,
    ChatSession,
    DailyQuest,
    IntelArticle,
    Item,
    ItemImage,
    Journal,
    PendingChange,
    RefreshSession,
    Resume,
    ResumeChatMessage,
    ResumeChatThread,
    ResumeSnapshot,
    Tag,
    Task,
    User,
    UserAIConfig,
    UserAchievement,
    UserQuota,
    UsageRecord,
    item_tags,
)
from app.routers import (
    auth, admin, categories, chat, intel, items, journals,
    quests, resume, rtc, stats, tags, tasks, user_config,
)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    # schema 由容器 entrypoint 的 `alembic upgrade head` 负责创建/迁移；
    # 旧 SQLite 的 create_all + ensure_column + date() 清洗已废弃。

    # v260729：首启确保超级管理员账号存在（口令哈希入库，首登强制改密）
    from app.utils.seed import ensure_superadmin
    await ensure_superadmin()

    # 每日 AI 资讯定时生成（APScheduler）
    scheduler = None
    if settings.INTEL_ENABLED:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        from app.services.intel import scheduled_generate_intel

        scheduler = AsyncIOScheduler(timezone=settings.INTEL_TZ)
        scheduler.add_job(
            scheduled_generate_intel,
            CronTrigger(hour=settings.INTEL_CRON_HOUR, minute=settings.INTEL_CRON_MINUTE),
            id="intel_daily",
            coalesce=True,         # 错过的多次只补跑一次
            max_instances=1,       # 绝不并发跑两个 Agent
            misfire_grace_time=3600,
        )
        scheduler.start()

    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title="DailyStuff API",
    description="Item management backend for DailyStuff",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# CORS – allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────
app.include_router(auth.router, tags=["auth"])
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(items.router)
app.include_router(stats.router)
app.include_router(quests.router)
app.include_router(journals.router)
app.include_router(intel.router)
app.include_router(tasks.router)
app.include_router(chat.router)
app.include_router(rtc.router)
app.include_router(resume.router)
app.include_router(user_config.router)
app.include_router(admin.router)

# ── Static Files ───────────────────────────────────────────────────────
# 修正：原代码 getattr(settings, 'upload_dir', ...) 用了小写属性名，
# pydantic 字段是 UPLOAD_DIR，导致环境变量永远改不了静态服务目录（文件写到
# UPLOAD_DIR 但 /uploads 仍从默认 'uploads' 读 → 部署挂载卷时图片 404）。
UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
