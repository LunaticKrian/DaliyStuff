"""站点管理后台（仅 is_admin）。用户管理 / 配置可见性 / 配额 / 用量统计 / 审计日志。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit import AuditLog
from app.models.quota import UserQuota
from app.models.usage import UsageRecord
from app.models.user import User
from app.models.user_ai_config import UserAIConfig
from app.schemas.admin import (
    AdminAiConfig,
    AdminUser,
    AdminUserUpdate,
    PaginatedAudit,
    QuotaResponse,
    QuotaUpdate,
    UsageSummary,
)
from app.utils.crypto import decrypt, mask_key
from app.utils.deps import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

_MONTH_COND = func.strftime("%Y-%m", UsageRecord.created_at) == func.strftime("%Y-%m", "now")


async def _audit(
    db: AsyncSession, *, actor_id: int, action: str,
    target_type: str | None = None, target_id: int | None = None,
    detail: dict | None = None, ip: str | None = None,
) -> None:
    db.add(AuditLog(
        actor_id=actor_id, action=action, target_type=target_type,
        target_id=target_id, detail=detail or {}, ip=ip,
    ))


async def _month_usage_map(db: AsyncSession) -> dict[int, tuple[int, float]]:
    rows = (await db.execute(
        select(
            UsageRecord.user_id,
            func.coalesce(func.sum(UsageRecord.input_tokens + UsageRecord.output_tokens), 0),
            func.coalesce(func.sum(UsageRecord.cost_usd), 0.0),
        ).where(_MONTH_COND).group_by(UsageRecord.user_id)
    )).all()
    return {r[0]: (int(r[1] or 0), float(r[2] or 0.0)) for r in rows}


@router.get("/users", response_model=list[AdminUser])
async def list_users(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUser]:
    users = (await db.execute(select(User).order_by(User.id))).scalars().all()
    configs = {
        c.user_id: c
        for c in (await db.execute(select(UserAIConfig))).scalars().all()
    }
    usage = await _month_usage_map(db)
    out: list[AdminUser] = []
    for u in users:
        cfg = configs.get(u.id)
        toks, cost = usage.get(u.id, (0, 0.0))
        out.append(AdminUser(
            id=u.id, username=u.username, email=u.email,
            is_admin=u.is_admin, disabled=u.disabled,
            has_config=cfg is not None and bool(cfg.model and cfg.base_url and cfg.api_key_enc),
            model=cfg.model if cfg else "",
            tokens_month=toks, cost_month=cost, created_at=u.created_at,
        ))
    return out


@router.patch("/users/{user_id}", response_model=AdminUser)
async def update_user(
    user_id: int,
    body: AdminUserUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    detail: dict = {}
    if body.is_admin is not None and body.is_admin != user.is_admin:
        detail["is_admin"] = {"from": user.is_admin, "to": body.is_admin}
        user.is_admin = body.is_admin
    if body.disabled is not None and body.disabled != user.disabled:
        detail["disabled"] = {"from": user.disabled, "to": body.disabled}
        user.disabled = body.disabled
    if detail:
        await _audit(
            db, actor_id=admin.id, action="user.update",
            target_type="user", target_id=user_id, detail=detail,
            ip=request.client.host if request.client else None,
        )
    await db.commit()
    await db.refresh(user)
    cfg = (await db.execute(select(UserAIConfig).where(UserAIConfig.user_id == user_id))).scalar_one_or_none()
    toks, cost = (await _month_usage_map(db)).get(user_id, (0, 0.0))
    return AdminUser(
        id=user.id, username=user.username, email=user.email,
        is_admin=user.is_admin, disabled=user.disabled,
        has_config=cfg is not None and bool(cfg.model and cfg.base_url and cfg.api_key_enc),
        model=cfg.model if cfg else "",
        tokens_month=toks, cost_month=cost, created_at=user.created_at,
    )


@router.get("/users/{user_id}/ai-config", response_model=AdminAiConfig)
async def get_user_ai_config(
    user_id: int,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAiConfig:
    row = (await db.execute(
        select(UserAIConfig).where(UserAIConfig.user_id == user_id)
    )).scalar_one_or_none()
    await _audit(
        db, actor_id=admin.id, action="config.view",
        target_type="user", target_id=user_id, detail={"had_config": row is not None},
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "该用户未配置 AI")
    plain = decrypt(row.api_key_enc)
    return AdminAiConfig(
        provider=row.provider, model=row.model, base_url=row.base_url,
        api_key_masked=mask_key(plain) if plain else "", has_key=bool(plain),
        max_turns=row.max_turns, max_budget_usd=row.max_budget_usd,
        system_prompt_extra=row.system_prompt_extra, enabled=row.enabled,
    )


@router.put("/quota/{user_id}", response_model=QuotaResponse)
async def set_quota(
    user_id: int,
    body: QuotaUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> QuotaResponse:
    if await db.get(User, user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    q = (await db.execute(select(UserQuota).where(UserQuota.user_id == user_id))).scalar_one_or_none()
    if q is None:
        q = UserQuota(user_id=user_id)
        db.add(q)
    detail: dict = {}
    if body.monthly_token_cap is not None:
        detail["monthly_token_cap"] = {"from": q.monthly_token_cap, "to": body.monthly_token_cap}
        q.monthly_token_cap = body.monthly_token_cap
    if body.monthly_cost_cap_usd is not None:
        detail["monthly_cost_cap_usd"] = {"from": q.monthly_cost_cap_usd, "to": body.monthly_cost_cap_usd}
        q.monthly_cost_cap_usd = body.monthly_cost_cap_usd
    await _audit(
        db, actor_id=admin.id, action="quota.update",
        target_type="user", target_id=user_id, detail=detail,
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(q)
    return QuotaResponse(
        user_id=q.user_id,
        monthly_token_cap=q.monthly_token_cap,
        monthly_cost_cap_usd=q.monthly_cost_cap_usd,
    )


@router.get("/usage", response_model=UsageSummary)
async def usage_summary(
    user_id: int | None = None,
    agent_type: str | None = None,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> UsageSummary:
    filters = []
    if user_id is not None:
        filters.append(UsageRecord.user_id == user_id)
    if agent_type:
        filters.append(UsageRecord.agent_type == agent_type)

    tok_stmt = select(func.coalesce(func.sum(UsageRecord.input_tokens + UsageRecord.output_tokens), 0))
    cost_stmt = select(func.coalesce(func.sum(UsageRecord.cost_usd), 0.0))
    if filters:
        tok_stmt = tok_stmt.where(*filters)
        cost_stmt = cost_stmt.where(*filters)
    total_tokens = (await db.scalar(tok_stmt)) or 0
    total_cost = (await db.scalar(cost_stmt)) or 0.0

    async def _group(col):
        stmt = select(
            col,
            func.coalesce(func.sum(UsageRecord.input_tokens + UsageRecord.output_tokens), 0),
            func.coalesce(func.sum(UsageRecord.cost_usd), 0.0),
        ).group_by(col)
        if filters:
            stmt = stmt.where(*filters)
        rows = (await db.execute(stmt)).all()
        out = []
        tk_sum = int(total_tokens or 0)
        for name, toks, cost in rows:
            out.append({
                "name": name or "(unknown)", "tokens": int(toks or 0),
                "cost": round(float(cost or 0.0), 4),
                "pct": round(int(toks or 0) / tk_sum * 100, 1) if tk_sum else 0.0,
            })
        out.sort(key=lambda x: x["tokens"], reverse=True)
        return out

    return UsageSummary(
        total_tokens=int(total_tokens or 0),
        total_cost=round(float(total_cost or 0.0), 4),
        by_model=await _group(UsageRecord.model),
        by_agent=await _group(UsageRecord.agent_type),
    )


@router.get("/audit", response_model=PaginatedAudit)
async def list_audit(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    action: str | None = None,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedAudit:
    where = []
    if action:
        where.append(AuditLog.action == action)
    count_stmt = select(func.count()).select_from(AuditLog)
    list_stmt = (
        select(AuditLog).order_by(AuditLog.id.desc())
        .offset((page - 1) * size).limit(size)
    )
    if where:
        count_stmt = count_stmt.where(*where)
        list_stmt = list_stmt.where(*where)
    total = (await db.scalar(count_stmt)) or 0
    rows = (await db.execute(list_stmt)).scalars().all()
    return PaginatedAudit(items=list(rows), total=int(total), page=page, size=size)
