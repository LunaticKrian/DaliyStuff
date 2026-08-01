"""Alembic 运行环境。

- target_metadata = app.database.Base.metadata；
- 运行期应用用 asyncmy，迁移这里用 sync pymysql（从同一 DATABASE_URL 派生），env.py 最简最稳；
- `import app.models` 注册全部模型（与 main.py 的导入一致），autogenerate 才看得到所有表。
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.config import settings
from app.database import Base
import app.models  # noqa: F401  注册所有模型到 Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 运行期 asyncmy → 迁移 sync pymysql，单一事实源 = settings.DATABASE_URL
sync_url = settings.DATABASE_URL.replace("+asyncmy", "+pymysql")
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：只生成 SQL，不连库。"""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：连库执行。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
