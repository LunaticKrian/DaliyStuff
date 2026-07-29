from pydantic import BaseModel, Field


class AiConfigResponse(BaseModel):
    provider: str = "anthropic"
    model: str = ""
    base_url: str = ""
    api_key_masked: str = ""        # sk-****1234；空表示未设置
    has_key: bool = False
    max_turns: int = 12
    max_budget_usd: float = 0.5
    system_prompt_extra: str | None = None
    enabled: bool = True
    configured: bool = False        # model/base_url/key 是否齐备


class AiConfigUpdate(BaseModel):
    provider: str | None = None
    model: str | None = Field(default=None, max_length=64)
    base_url: str | None = Field(default=None, max_length=255)
    # 明文 key；None / 空 / 含 **** 的掩码串 → 保留旧值（不覆盖）
    api_key: str | None = Field(default=None, max_length=512)
    max_turns: int | None = Field(default=None, ge=1, le=100)
    max_budget_usd: float | None = Field(default=None, ge=0, le=100)
    system_prompt_extra: str | None = Field(default=None, max_length=4000)
    enabled: bool | None = None


class AiConfigTestResult(BaseModel):
    ok: bool
    message: str
    model: str | None = None
    latency_ms: int | None = None
