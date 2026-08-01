from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+asyncmy://pixelpack:pixelpack@127.0.0.1:3306/pixelpack?charset=utf8mb4"
    SECRET_KEY: str = "dev-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    UPLOAD_DIR: str = "uploads"

    # ── 用户 AI 配置加密（per-user API Key 入库）──
    # 标准 Fernet 密钥（base64 urlsafe 32 字节）或任意口令；未配则从 SECRET_KEY 派生（仅单机）。
    ENCRYPTION_KEY: str | None = None
    # ── 超级管理员 seed（首启建账号；明文不入库，首登强制改密）──
    SUPERADMIN_USERNAME: str = "super-hero"
    SUPERADMIN_PASSWORD: str = "QazWsx1314520!"

    # ── 已废弃（v260729 起模型/key 改为 per-user，见 user_ai_configs 表）──
    # 保留字段仅为兼容旧 .env，不再作为模型源；Agent 已改为读取各用户自己的配置。
    ANTHROPIC_BASE_URL: str | None = None
    ANTHROPIC_AUTH_TOKEN: str | None = None
    ANTHROPIC_MODEL: str | None = None
    INTEL_ENABLED: bool = True              # 总开关，开发期可关
    INTEL_MAX_TURNS: int = 12               # Agent 单次最大轮数
    INTEL_MAX_BUDGET: float = 0.5           # 单次成本软上限 (USD)
    INTEL_TZ: str = "Asia/Shanghai"         # 调度时区
    INTEL_CRON_HOUR: int = 7                # 每日生成 - 小时
    INTEL_CRON_MINUTE: int = 0              # 每日生成 - 分钟
    # Agent 检索 / 产出参数（原魔法值：40 / 4-6）
    INTEL_SEARCH_LIMIT: int = 40            # search_ai_news 每次拉取的候选条数
    INTEL_MIN_ARTICLES: int = 4             # 单次产出情报下限
    INTEL_MAX_ARTICLES: int = 6             # 单次产出情报上限

    # ── 任务系统 ──
    TASK_DEFAULT_EXP: int = 10              # 手动添加任务的默认经验
    TASK_EXP_PER_LEVEL: int = 50            # 每多少经验升一级
    TASK_CATEGORIES: str = "study,work,life,health,other"
    TASK_AGENT_MAX_TURNS: int = 12          # 对话生成任务 Agent 单次最大轮数

    # ── 简历 / AI 编辑（冒险者履历 DOSSIER）──
    RESUME_AGENT_MAX_TURNS: int = 12        # 简历编辑 Agent 单次最大轮数

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
