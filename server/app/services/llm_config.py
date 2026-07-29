"""集中三处 Agent 的 per-user LLM 配置解析。

原先各 Agent 在模块加载时把 settings.ANTHROPIC_* 写进 os.environ（进程级全局，并发用户会互相
覆盖 key/model —— 有竞态）。本模块改为：读 user_ai_configs → 解密 key → 构造 per-query 的
``ClaudeAgentOptions(env=…, model=…, max_turns=…, max_budget_usd=…)``。SDK 子进程 env =
{**继承的 os.environ, **options.env}，每次 query 各自独立，零竞态。
"""
import logging
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.quota import UserQuota
from app.models.usage import UsageRecord
from app.models.user_ai_config import UserAIConfig
from app.services import pricing
from app.utils.crypto import decrypt

logger = logging.getLogger(__name__)


@dataclass
class UserLLMSnapshot:
    model: str
    base_url: str
    api_key: str            # 已解密明文（仅存在于本次请求内存中）
    max_turns: int
    max_budget_usd: float
    system_prompt_extra: str | None


async def load_snapshot(db: AsyncSession, user_id: int) -> UserLLMSnapshot | None:
    """读当前用户已启用的 AI 配置并解密 key。无配置 / 未启用 / 字段缺失 → None。"""
    row = (
        await db.execute(select(UserAIConfig).where(UserAIConfig.user_id == user_id))
    ).scalar_one_or_none()
    if row is None or not row.enabled:
        return None
    if not row.model or not row.base_url or not row.api_key_enc:
        return None
    key = decrypt(row.api_key_enc)
    if not key:
        return None
    return UserLLMSnapshot(
        model=row.model,
        base_url=row.base_url,
        api_key=key,
        max_turns=row.max_turns or settings.TASK_AGENT_MAX_TURNS,
        max_budget_usd=row.max_budget_usd if row.max_budget_usd is not None else settings.INTEL_MAX_BUDGET,
        system_prompt_extra=row.system_prompt_extra,
    )


def sdk_env(snap: UserLLMSnapshot) -> dict:
    """供 claude-agent-sdk 子进程继承的 Anthropic 兼容环境变量。"""
    return {
        "ANTHROPIC_BASE_URL": snap.base_url,
        "ANTHROPIC_AUTH_TOKEN": snap.api_key,
        "ANTHROPIC_MODEL": snap.model,
    }


def with_extra_prompt(base: str, snap: UserLLMSnapshot) -> str:
    """把用户附加 system_prompt_extra 拼到 Agent 内置 prompt 之后（不覆盖职能提示）。"""
    extra = (snap.system_prompt_extra or "").strip()
    if not extra:
        return base
    return f"{base}\n\n— 用户附加指令 —\n{extra}"


# ── 配额 / 用量 ────────────────────────────────────────────────────────
async def month_usage(db: AsyncSession, user_id: int) -> tuple[int, float]:
    """当月（自然月）已用 token 总量 / 成本。"""
    res = await db.execute(
        select(
            func.coalesce(func.sum(UsageRecord.input_tokens + UsageRecord.output_tokens), 0),
            func.coalesce(func.sum(UsageRecord.cost_usd), 0.0),
        ).where(
            UsageRecord.user_id == user_id,
            func.strftime("%Y-%m", UsageRecord.created_at) == func.strftime("%Y-%m", "now"),
        )
    )
    toks, cost = res.one()
    return int(toks or 0), float(cost or 0.0)


async def get_quota(db: AsyncSession, user_id: int) -> UserQuota | None:
    return (
        await db.execute(select(UserQuota).where(UserQuota.user_id == user_id))
    ).scalar_one_or_none()


async def check_quota(db: AsyncSession, user_id: int) -> tuple[bool, str]:
    """超限 → (False, 原因)；否则 (True, '')。无配额行视为不限。"""
    q = await get_quota(db, user_id)
    if q is None:
        return True, ""
    used_tok, used_cost = await month_usage(db, user_id)
    if q.monthly_token_cap is not None and used_tok >= q.monthly_token_cap:
        return False, f"已达本月 token 上限（{used_tok}/{q.monthly_token_cap}）"
    if q.monthly_cost_cap_usd is not None and used_cost >= q.monthly_cost_cap_usd:
        return False, f"已达本月成本上限（${used_cost:.2f}/${q.monthly_cost_cap_usd:.2f}）"
    return True, ""


async def record_usage(
    db: AsyncSession, *, user_id: int, agent_type: str, model: str,
    result_msg, duration_ms: int | None,
) -> None:
    """从 SDK ResultMessage.model_usage 解析 token、估成本、写 usage_records。

    model_usage 可能是 ``{input_tokens, output_tokens, ...}`` 或 ``{<model>: {...}}``，都兼容。
    """
    mu = getattr(result_msg, "model_usage", None) or {}
    inp = out = cr = cw = 0
    if isinstance(mu, dict) and mu:
        vals = mu
        if all(isinstance(v, dict) for v in mu.values()):
            vals = next(iter(mu.values())) or {}
        inp = int(vals.get("input_tokens") or vals.get("input") or 0)
        out = int(vals.get("output_tokens") or vals.get("output") or 0)
        cr = int(vals.get("cache_read_input_tokens") or vals.get("cache_read_tokens") or 0)
        cw = int(vals.get("cache_creation_input_tokens") or vals.get("cache_write_tokens") or 0)
    cost = pricing.estimate_cost(model, inp, out, cr, cw)
    db.add(UsageRecord(
        user_id=user_id, agent_type=agent_type, model=model or "",
        input_tokens=inp, output_tokens=out, cache_read_tokens=cr, cache_write_tokens=cw,
        cost_usd=cost, duration_ms=duration_ms,
    ))
    await db.commit()
