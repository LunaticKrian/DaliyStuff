"""当前用户的 AI 模型配置（per-user）：读 / 写 / 测试连接。

- GET  /api/me/ai-config        返回配置，api_key 永远掩码（sk-****1234）。
- PUT  /api/me/ai-config        upsert；api_key 为空或掩码串则保留旧值。
- POST /api/me/ai-config/test   用（可覆盖的）配置跑一次极小探测，校验 model/url/key。
"""
import time

from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.user_ai_config import UserAIConfig
from app.schemas.user_config import AiConfigResponse, AiConfigTestResult, AiConfigUpdate
from app.utils.crypto import decrypt, encrypt, mask_key
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/me", tags=["me"])


async def _get_row(db: AsyncSession, user_id: int) -> UserAIConfig | None:
    return (
        await db.execute(select(UserAIConfig).where(UserAIConfig.user_id == user_id))
    ).scalar_one_or_none()


def _to_response(row: UserAIConfig | None) -> AiConfigResponse:
    if row is None:
        return AiConfigResponse(configured=False)
    plain = decrypt(row.api_key_enc)
    return AiConfigResponse(
        provider=row.provider,
        model=row.model,
        base_url=row.base_url,
        api_key_masked=mask_key(plain) if plain else "",
        has_key=bool(plain),
        max_turns=row.max_turns,
        max_budget_usd=row.max_budget_usd,
        system_prompt_extra=row.system_prompt_extra,
        enabled=row.enabled,
        configured=bool(row.model and row.base_url and row.api_key_enc),
    )


@router.get("/ai-config", response_model=AiConfigResponse)
async def get_ai_config(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AiConfigResponse:
    return _to_response(await _get_row(db, user.id))


@router.put("/ai-config", response_model=AiConfigResponse)
async def update_ai_config(
    body: AiConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AiConfigResponse:
    row = await _get_row(db, user.id)
    if row is None:
        row = UserAIConfig(user_id=user.id)
        db.add(row)
    if body.provider is not None:
        row.provider = body.provider
    if body.model is not None:
        row.model = body.model
    if body.base_url is not None:
        row.base_url = body.base_url
    if body.max_turns is not None:
        row.max_turns = body.max_turns
    if body.max_budget_usd is not None:
        row.max_budget_usd = body.max_budget_usd
    if body.system_prompt_extra is not None:
        row.system_prompt_extra = (body.system_prompt_extra or "").strip() or None
    if body.enabled is not None:
        row.enabled = body.enabled
    # 仅当传入「非空且非掩码」的 key 时才覆盖，避免前端误回填掩码串清掉密钥
    if body.api_key and "****" not in body.api_key:
        row.api_key_enc = encrypt(body.api_key)
    await db.commit()
    await db.refresh(row)
    return _to_response(row)


@router.post("/ai-config/test", response_model=AiConfigTestResult)
async def test_ai_config(
    body: AiConfigUpdate | None = Body(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AiConfigTestResult:
    row = await _get_row(db, user.id)
    model = (body.model if body and body.model else (row.model if row else "")) or ""
    base_url = (body.base_url if body and body.base_url else (row.base_url if row else "")) or ""
    if body and body.api_key and "****" not in body.api_key:
        key = body.api_key          # 表单里新填的明文
    elif row and row.api_key_enc:
        key = decrypt(row.api_key_enc)
    else:
        key = ""
    if not (model and base_url and key):
        return AiConfigTestResult(ok=False, message="配置不完整：model / base_url / api_key 均必填")

    try:
        from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

        t0 = time.monotonic()
        options = ClaudeAgentOptions(
            system_prompt="You are a connectivity probe. Reply with exactly: OK",
            env={
                "ANTHROPIC_BASE_URL": base_url,
                "ANTHROPIC_AUTH_TOKEN": key,
                "ANTHROPIC_MODEL": model,
            },
            model=model,
            max_turns=1,
        )
        subtype = None
        async for msg in query(prompt="ping", options=options):
            if isinstance(msg, ResultMessage):
                subtype = msg.subtype
        ms = int((time.monotonic() - t0) * 1000)
        if subtype == "success":
            return AiConfigTestResult(ok=True, message="连接成功", model=model, latency_ms=ms)
        return AiConfigTestResult(
            ok=False, message=f"模型返回非成功状态（{subtype}）", model=model, latency_ms=ms,
        )
    except Exception as e:  # noqa: BLE001
        return AiConfigTestResult(ok=False, message=f"连接失败：{e}", model=model)
