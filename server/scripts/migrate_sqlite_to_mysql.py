"""一次性 ETL：把旧 SQLite data.db 数据迁入 MySQL。

在 server/ 目录下运行（使 ./data.db 与 import app.* 都可用）：

    # 1. 先确保 MySQL 已起、schema 已由 `alembic upgrade head` 建好
    # 2. 执行迁移
    DATABASE_URL='mysql+asyncmy://pixelpack:pixelpack@127.0.0.1:3306/pixelpack?charset=utf8mb4' \
        python scripts/migrate_sqlite_to_mysql.py

说明：
- 源 = SQLite（stdlib sqlite3，只读）；目标 = MySQL（SQLAlchemy sync pymysql，从 DATABASE_URL 派生）。
- 表顺序用 Base.metadata.sorted_tables（拓扑序，满足 FK 依赖）；装载期间 SET FOREIGN_KEY_CHECKS=0。
- 显式保留原主键 id，维护 FK 关系；AUTO_INCREMENT 自动跟上 max(id)。
- 幂等：每张表先 delete 再 insert，可重跑。
- 末尾逐表 COUNT 源 vs 目标校验。
"""
import json
import os
import sqlite3
import sys
from datetime import date, datetime

# 使 `python scripts/xxx.py` 时能 import app.*（把 server/ 父目录加入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from sqlalchemy import create_engine

# 必须在导入 app.* 前设置 DATABASE_URL（目标库）
os.environ.setdefault(
    "DATABASE_URL",
    "mysql+asyncmy://pixelpack:pixelpack@127.0.0.1:3306/pixelpack?charset=utf8mb4",
)

from app.config import settings
from app.database import Base
import app.models  # noqa: F401  注册所有模型，Base.metadata.sorted_tables 才全

SQLITE_PATH = os.environ.get("SQLITE_PATH", "./data.db")


def coerce(value, col_type):
    """SQLite 文本存储 → MySQL 强类型的显式映射。"""
    if value is None:
        return None
    # JSON：SQLite 存 TEXT，MySQL JSON 需合法 JSON 串/dict
    if isinstance(col_type, sa.JSON) and isinstance(value, str):
        return json.loads(value)
    # DateTime：SQLite 存 ISO 文本 → datetime
    if isinstance(col_type, sa.DateTime) and isinstance(value, str):
        return datetime.fromisoformat(value)
    # Date：脏数据 'YYYY-MM-DD HH:MM:SS' → 'YYYY-MM-DD'（等价旧 date() 清洗）
    if isinstance(col_type, sa.Date) and isinstance(value, str):
        return date.fromisoformat(value[:10])
    # Boolean / Integer / String：SQLite 存 0/1 或文本，MySQL 直接接收
    return value


def main() -> int:
    if not os.path.exists(SQLITE_PATH):
        print(f"[ERR] 源 SQLite 不存在：{SQLITE_PATH}", file=sys.stderr)
        return 1

    sync_url = settings.DATABASE_URL.replace("+asyncmy", "+pymysql")
    target = create_engine(sync_url, future=True)
    src = sqlite3.connect(SQLITE_PATH)
    src.row_factory = sqlite3.Row

    print(f"源: sqlite://{SQLITE_PATH}")
    print(f"目标: {sync_url.rsplit('@', 1)[0]}@***")
    print("-" * 60)

    mismatches = 0
    with target.begin() as conn:
        conn.execute(sa.text("SET FOREIGN_KEY_CHECKS=0"))
        for table in Base.metadata.sorted_tables:
            tname = table.name
            try:
                rows = src.execute(f"SELECT * FROM {tname}").fetchall()
            except sqlite3.OperationalError as e:
                print(f"[SKIP] {tname}: 源表不存在 ({e})")
                continue
            if not rows:
                print(f"{tname:28s} 0 -> 0")
                continue
            data = [
                {c.name: coerce(r[c.name], c.type) for c in table.columns}
                for r in rows
            ]
            conn.execute(table.delete())
            conn.execute(table.insert(), data)
            tgt = conn.execute(sa.text(f"SELECT COUNT(*) FROM {tname}")).scalar()
            flag = "OK" if tgt == len(rows) else "MISMATCH"
            if tgt != len(rows):
                mismatches += 1
            print(f"{tname:28s} {len(rows):>5} -> {tgt:<5} {flag}")
        conn.execute(sa.text("SET FOREIGN_KEY_CHECKS=1"))

    print("-" * 60)
    print("DONE" if mismatches == 0 else f"DONE with {mismatches} mismatch(es)")
    return 0 if mismatches == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
