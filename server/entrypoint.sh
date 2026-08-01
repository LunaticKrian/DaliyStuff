#!/bin/sh
set -e
# schema 迁移：失败则容器退出（exit 非 0），避免带旧 schema 病态服务。
# alembic.ini 在 /app，env.py 从 DATABASE_URL 派生 sync pymysql URL。
alembic upgrade head

# exec 让 uvicorn 接管 PID 1，正确接收 SIGTERM。
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 \
     --log-config app/uvicorn_log_config.json
