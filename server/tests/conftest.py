"""Pytest 配置：隔离的 SQLite 测试库 + 异步 httpx 客户端。

注意：必须在导入 `app.*` 之前设置环境变量，使 settings 读取临时 DB、关闭 intel 调度。
不触发 app lifespan（避免 APScheduler）；表由 fixture 显式 create/drop。
"""
import os
import tempfile

_TMP_DB = os.path.join(tempfile.gettempdir(), "pixelpack_auth_test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_DB}"
os.environ.setdefault("INTEL_ENABLED", "false")
os.environ.setdefault("SECRET_KEY", "test-secret")

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, engine
from app.main import app  # noqa: E402 – 在环境变量设置后导入


@pytest.fixture()
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
