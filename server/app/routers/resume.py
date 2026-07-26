"""冒险者履历 DOSSIER · REST + SSE 路由。

prefix /api/resume。所有端点需登录，并校验简历归属于当前用户。
"""
import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory, get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import (
    ChatRequest,
    InlinePolishRequest,
    InlinePolishResponse,
    ResumeCreate,
    ResumeListItem,
    ResumeMetaUpdate,
    ResumeResponse,
    ResumeUpdate,
    ThreadCreate,
    VersionDiff,
    VersionItem,
)
from app.services import resume as svc
from app.services import resume_agent
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/resume", tags=["resume"])

# 同一线程不并发跑两个 Agent 子进程（同 chat.py）
_thread_locks: dict[int, asyncio.Lock] = {}
_locks_guard = asyncio.Lock()


async def _get_lock(thread_id: int) -> asyncio.Lock:
    async with _locks_guard:
        if thread_id not in _thread_locks:
            _thread_locks[thread_id] = asyncio.Lock()
        return _thread_locks[thread_id]


async def _require_resume(db: AsyncSession, resume_id: int, user: User) -> Resume:
    r = await svc.get_resume(db, resume_id, user.id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "简历不存在")
    return r


def _conflict(e: Exception):
    return HTTPException(status.HTTP_409_CONFLICT, str(e))


def _not_found(e: Exception):
    return HTTPException(status.HTTP_404_NOT_FOUND, str(e))


# ── 简历 CRUD ───────────────────────────────────────────────────────────
@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_resume(
    body: ResumeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    r = await svc.create_resume(db, current_user.id, body.title, body.lang, body.template)
    return await svc.read_full(db, r)


@router.get("", response_model=list[ResumeListItem])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_mine(db, current_user.id)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    r = await _require_resume(db, resume_id, current_user)
    return await svc.read_full(db, r)


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    body: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    r = await _require_resume(db, resume_id, current_user)
    await svc.update_resume(db, r, body.data, body.summary)
    return await svc.read_full(db, r)


@router.patch("/{resume_id}/meta", response_model=ResumeResponse)
async def update_meta(
    resume_id: int,
    body: ResumeMetaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """切换模板 / 当前语言。不生成快照、不前进 revision。"""
    r = await _require_resume(db, resume_id, current_user)
    await svc.update_meta(db, r, body.lang, body.template)
    return await svc.read_full(db, r)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    r = await _require_resume(db, resume_id, current_user)
    await svc.delete_resume(db, r)


# ── 对话线程 ────────────────────────────────────────────────────────────
@router.post("/{resume_id}/threads", status_code=status.HTTP_201_CREATED)
async def create_thread(
    resume_id: int,
    _body: ThreadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _require_resume(db, resume_id, current_user)
    t = await svc.create_thread(db, resume_id)
    return {"id": t.id, "resumeId": resume_id}


@router.get("/{resume_id}/threads/{thread_id}/messages")
async def list_messages(
    resume_id: int,
    thread_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await _require_resume(db, resume_id, current_user)
    t = await svc.get_thread(db, thread_id, current_user.id)
    if t is None or t.resume_id != resume_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "对话线程不存在")
    msgs = await svc.list_messages(db, thread_id)
    return [{"id": m.id, "role": m.role, "content": m.content, "createdAt": m.created_at} for m in msgs]


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/{resume_id}/threads/{thread_id}/chat")
async def chat(
    resume_id: int,
    thread_id: int,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    await _require_resume(db, resume_id, current_user)
    t = await svc.get_thread(db, thread_id, current_user.id)
    if t is None or t.resume_id != resume_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "对话线程不存在")

    # 落库用户消息 + 取历史（必须在 StreamingResponse 返回前完成）
    await svc.add_message(db, thread_id, "user", body.content)
    await db.commit()
    prompt = await svc.history_prompt(db, thread_id)
    group_id = f"g_{uuid.uuid4().hex[:12]}"
    uid, rid, tid = current_user.id, resume_id, thread_id
    lock = await _get_lock(thread_id)

    async def event_stream():
        yield _sse({"type": "start", "groupId": group_id})
        full_text: list[str] = []
        async with lock:
            try:
                async for ev in resume_agent.run_agent(uid, rid, prompt, group_id):
                    if ev["type"] == "delta":
                        full_text.append(ev["text"])
                    yield _sse(ev)
            except Exception as e:  # noqa: BLE001
                yield _sse({"type": "error", "message": str(e)})

        # 落库助手消息（独立 session）
        text = "".join(full_text).strip()
        async with async_session_factory() as s2:
            await svc.add_message(s2, tid, "assistant", text or "(无回复)")
            await s2.commit()
        yield _sse({"type": "end", "groupId": group_id})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.post("/{resume_id}/inline-polish", response_model=InlinePolishResponse)
async def inline_polish(
    resume_id: int,
    body: InlinePolishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InlinePolishResponse:
    """字段内联润色：同步跑一次 Agent，产出一条 pending 并返回。"""
    await _require_resume(db, resume_id, current_user)
    group_id = f"g_{uuid.uuid4().hex[:12]}"
    field_hint = f"字段 {body.field}" if body.field else "整条"
    prompt = (
        f"请润色简历 {body.section} 板块第 {body.index} 条的 {field_hint}。"
        f"要求：{body.instruction}。直接调用合适的工具（update_profile 或 update_entry）"
        f"产出一条拟变更，不要额外解释。"
    )
    pending_id: int | None = None
    async for ev in resume_agent.run_agent(current_user.id, resume_id, prompt, group_id):
        if ev["type"] == "tool_call":
            pending_id = ev["pending_id"]
            break  # 内联润色只需一条

    if pending_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "AI 未能产出变更，请换种说法再试")

    async with async_session_factory() as s2:
        p = await svc.get_pending(s2, resume_id, pending_id)
        if p is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "拟变更不存在")
        return InlinePolishResponse(pending=svc.to_pending_response(p))


# ── 待确认变更 ──────────────────────────────────────────────────────────
@router.get("/{resume_id}/pending")
async def list_pending(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_resume(db, resume_id, current_user)
    return await svc.list_pending(db, resume_id)


@router.post("/{resume_id}/pending/{pending_id}/accept", response_model=ResumeResponse)
async def accept_pending(
    resume_id: int,
    pending_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    r = await _require_resume(db, resume_id, current_user)
    p = await svc.get_pending(db, resume_id, pending_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "拟变更不存在")
    try:
        await svc.accept_one(db, r, p)
    except svc.ResumeConflict as e:
        raise _conflict(e) from e
    return await svc.read_full(db, r)


@router.post("/{resume_id}/pending/group/{group_id}/accept", response_model=ResumeResponse)
async def accept_group(
    resume_id: int,
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    r = await _require_resume(db, resume_id, current_user)
    try:
        await svc.accept_group(db, r, group_id)
    except svc.ResumeConflict as e:
        raise _conflict(e) from e
    except svc.ResumeNotFound as e:
        raise _not_found(e) from e
    return await svc.read_full(db, r)


@router.delete("/{resume_id}/pending/{pending_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deny_pending(
    resume_id: int,
    pending_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await _require_resume(db, resume_id, current_user)
    p = await svc.get_pending(db, resume_id, pending_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "拟变更不存在")
    await svc.deny_one(db, p)


@router.delete("/{resume_id}/pending/group/{group_id}")
async def deny_group(
    resume_id: int,
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _require_resume(db, resume_id, current_user)
    n = await svc.deny_group(db, resume_id, group_id)
    return {"denied": n}


# ── 版本 ───────────────────────────────────────────────────────────────
@router.get("/{resume_id}/versions", response_model=list[VersionItem])
async def list_versions(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_resume(db, resume_id, current_user)
    return await svc.list_versions(db, resume_id)


@router.post("/{resume_id}/revert/{revision}", response_model=ResumeResponse)
async def revert(
    resume_id: int,
    revision: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    r = await _require_resume(db, resume_id, current_user)
    try:
        await svc.revert(db, r, revision)
    except svc.ResumeNotFound as e:
        raise _not_found(e) from e
    return await svc.read_full(db, r)


@router.get("/{resume_id}/versions/{a}/diff/{b}", response_model=VersionDiff)
async def diff_versions(
    resume_id: int,
    a: int,
    b: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VersionDiff:
    await _require_resume(db, resume_id, current_user)
    try:
        sections = await svc.diff_versions(db, resume_id, a, b)
    except svc.ResumeNotFound as e:
        raise _not_found(e) from e
    return VersionDiff(a=a, b=b, sections=sections)
