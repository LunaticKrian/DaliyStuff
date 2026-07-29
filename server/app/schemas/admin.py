from datetime import datetime

from pydantic import BaseModel, Field


class AdminUser(BaseModel):
    id: int
    username: str
    email: str | None
    is_admin: bool
    disabled: bool
    has_config: bool
    model: str
    tokens_month: int
    cost_month: float
    created_at: datetime


class AdminUserUpdate(BaseModel):
    is_admin: bool | None = None
    disabled: bool | None = None


class AdminAiConfig(BaseModel):
    """管理员视角的某用户 AI 配置（key 永远掩码）。"""
    provider: str
    model: str
    base_url: str
    api_key_masked: str
    has_key: bool
    max_turns: int
    max_budget_usd: float
    system_prompt_extra: str | None
    enabled: bool


class QuotaUpdate(BaseModel):
    monthly_token_cap: int | None = Field(default=None, ge=0)
    monthly_cost_cap_usd: float | None = Field(default=None, ge=0)


class QuotaResponse(BaseModel):
    user_id: int
    monthly_token_cap: int | None
    monthly_cost_cap_usd: float | None


class UsageSummary(BaseModel):
    total_tokens: int
    total_cost: float
    by_model: list[dict]
    by_agent: list[dict]


class AuditLogRow(BaseModel):
    id: int
    actor_id: int
    action: str
    target_type: str | None
    target_id: int | None
    detail: dict
    ip: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedAudit(BaseModel):
    items: list[AuditLogRow]
    total: int
    page: int
    size: int
