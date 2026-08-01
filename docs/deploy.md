# PixelPack 部署说明

> 本文档记录部署相关的环境变量与注意事项。随特性迭代持续更新。

## 后端环境变量（`server/.env`）

模板见 `server/.env.example`：在服务器上 `cp server/.env.example server/.env` 后填真实值。
`.env` 不进 git / 不进镜像，由 `docker-compose.yml` 的 `env_file` 在运行时注入。

> ⚠️ `DATABASE_URL` 与 `UPLOAD_DIR` 已在 `docker-compose.yml` 的 `environment` 中固定（`DATABASE_URL` 指向 compose 内网 `mysql:3306/pixelpack`），不要在 `.env` 覆盖。但 MySQL 口令 `MYSQL_ROOT_PASSWORD` / `MYSQL_APP_PASSWORD` 必须在 `.env` 设置（compose 读取）。

### 必填 / 推荐

| 变量 | 说明 |
|---|---|
| `SECRET_KEY` | JWT 签名密钥。生产必须改成随机长串。 |
| `MYSQL_ROOT_PASSWORD` / `MYSQL_APP_PASSWORD` | MySQL root 口令与 app 用户（`pixelpack`）口令。compose 首启据此自动建 `pixelpack` 库 + `pixelpack` 用户并授权。生产务必改成强口令。 |
| `ENCRYPTION_KEY` | **v260729** 用户 API Key 加密主密钥（Fernet）。生产请显式生成：`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`。留空则从 `SECRET_KEY` 派生（仅单机自部署）。**轮换该 key 后旧密文无法解密，用户需重填 API Key。** |
| `SUPERADMIN_USERNAME` / `SUPERADMIN_PASSWORD` | **v260729** 首启自动创建的超级管理员账号（明文不入库、首登强制改密）。默认 `super-hero` / `QazWsx1314520!`，生产务必覆盖。 |

### 每日 AI 资讯（定时任务）

| 变量 | 说明 |
|---|---|
| `INTEL_CRON_HOUR` / `INTEL_CRON_MINUTE` | 每日定时生成时刻（默认 07:00，`INTEL_TZ` 时区）。 |
| `INTEL_SEARCH_LIMIT` / `INTEL_MIN_ARTICLES` / `INTEL_MAX_ARTICLES` | 抓取候选条数 / 产出篇数上下限。 |
| `INTEL_ENABLED` | 总开关，开发期可关。 |

> v260729 起 intel 改 **per-user**：定时任务会遍历「已启用 AI 配置」的用户，各自用自己的 model/key 生成各自的每日资讯。

### 已废弃

`ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_MODEL` —— v260729 起模型 / key 迁移到每个用户的个人配置（前端「AI 配置」页，加密入库）。这三项仅为兼容旧 `.env` 保留，新部署无需填写。

## 数据库（MySQL）

- 服务由 `docker-compose.yml` 的 `mysql`（`mysql:8.4` LTS）提供；数据持久化到宿主 `./data/mysql`（容器 `/var/lib/mysql`）。
- **首启自动建库**：`MYSQL_DATABASE=pixelpack` + `MYSQL_USER=pixelpack` 由 mysql 镜像 entrypoint 自动创建库与用户并授权，无需手工 init。
- **schema 迁移**：`api` 容器 `entrypoint.sh` 启动时先跑 `alembic upgrade head` 再起 uvicorn；容器重启自动对齐。
- **持久化目录权限**：
  - 镜像 entrypoint 以 root 启动、首启自动 `chown` 给 mysql 用户（UID 999），空目录**无需手动 chown**。
  - CentOS / SELinux enforcing 主机：挂载已带 `:Z`（见 compose），自动打标签；若手改挂载点别漏 `:Z`。
  - `./data` 仍属 `app` 用户（UID 1000，给 api 写 uploads）；`./data/mysql` 属 mysql（999）—— 不同子目录不同属主，互不影响。
- **`docker compose down`（含 `-v`）不会删除 bind-mount 的宿主 `./data/mysql`**；只有手动删该目录才丢库。
- **从旧 SQLite 迁数据**（仅首次）：见 `server/scripts/migrate_sqlite_to_mysql.py`。流程：起 MySQL → `alembic upgrade head` 建表 → 跑 ETL → 逐表 COUNT 校验。旧 `server/data.db` 迁完暂存，验证一周后再删。

## v260729 迁移注意（.env → per-user）

- 旧 `ANTHROPIC_*` 不再作为模型源；如已在生产用过，迁移后需由各用户在前端填写自己的配置（或由管理员引导）。
- 首启由容器 entrypoint 跑 `alembic upgrade head` 自动建表/迁移 + 创建超级管理员（幂等；旧 SQLite 的手工补列已废弃）。
- 超管首次登录会要求改密。
