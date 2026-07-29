# PixelPack 部署说明

> 本文档记录部署相关的环境变量与注意事项。随特性迭代持续更新。

## 后端环境变量（`server/.env`）

模板见 `server/.env.example`：在服务器上 `cp server/.env.example server/.env` 后填真实值。
`.env` 不进 git / 不进镜像，由 `docker-compose.yml` 的 `env_file` 在运行时注入。

> ⚠️ `DATABASE_URL` 与 `UPLOAD_DIR` 已在 `docker-compose.yml` 的 `environment` 中固定指向 `/app/data`（持久化卷），不要在 `.env` 覆盖。

### 必填 / 推荐

| 变量 | 说明 |
|---|---|
| `SECRET_KEY` | JWT 签名密钥。生产必须改成随机长串。 |
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

## v260729 迁移注意（.env → per-user）

- 旧 `ANTHROPIC_*` 不再作为模型源；如已在生产用过，迁移后需由各用户在前端填写自己的配置（或由管理员引导）。
- 首启会自动建表 + 给 `users`/`intel_articles` 补列 + 创建超级管理员（幂等）。
- 超管首次登录会要求改密。
