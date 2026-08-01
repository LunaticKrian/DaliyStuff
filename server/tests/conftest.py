"""Pytest 配置：隔离的 MySQL 测试库 + 异步 httpx 客户端。

注意：必须在导入 `app.*` 之前设置环境变量，使 settings 读取测试库、关闭 intel 调度。
不触发 app lifespan（避免 APScheduler）；表由 fixture 显式 create/drop（与生产同方言）。

前置：测试库 pixelpack_test 需存在（建一次即可）。在 mysql 容器里执行：
    CREATE DATABASE IF NOT EXISTS pixelpack_test CHARACTER SET utf8mb4;
    GRANT ALL ON pixelpack_test.* TO 'pixelpack'@'%';   # 测试用同一 app 用户
可用 TEST_DATABASE_URL 覆盖（如改连 root 或别的 host）。
"""
import os

# 测试库（MySQL，与生产同方言，消除 sqlite/mysql 漂移）
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "mysql+asyncmy://pixelpack:pixelpack@127.0.0.1:3306/pixelpack_test?charset=utf8mb4",
)
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
    # 释放连接池：asyncmy 连接绑定创建它的 event loop，function 级 loop 关闭后
    # 池里残留连接无法 terminate（"Event loop is closed"）。每测后 dispose，下测新 loop 重建连接。
    await engine.dispose()
