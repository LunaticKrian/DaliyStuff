"""冒险者履历 DOSSIER · 业务层。

职责：
- 简历 CRUD + 版本快照（apply_and_snapshot：手动保存与 AI 接受共用同一落库函数）。
- 工具回放 compute_and_apply：把一条工具调用应用到 ResumeData 副本，产出 diff（越界/非法即 raise）。
- PendingChange：列出 / 接受（base_revision 乐观锁）/ 拒绝；整组接受在一个事务内顺序回放。
- 版本：时间线 / 回滚（追加新版本，历史不可变）/ 两版差异。
- 对话：线程 / 消息 / 历史拼装。
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import (
    PendingChange,
    Resume,
    ResumeChatMessage,
    ResumeChatThread,
    ResumeSnapshot,
)
from app.schemas.resume import (
    AddEntryArgs,
    AwardEntry,
    DeleteEntryArgs,
    PendingChangeResponse,
    ProjectEntry,
    ResumeData,
    ResumeListItem,
    ResumeResponse,
    SkillGroup,
    TimelineEntry,
    UpdateEntryArgs,
    UpdateProfileArgs,
    VersionItem,
)

logger = logging.getLogger(__name__)


class ResumeConflict(Exception):
    """base_revision 与当前版本不一致（并发冲突），路由层映射 409。"""


class ResumeNotFound(Exception):
    """简历/资源不存在或不属于当前用户，路由层映射 404。"""


# 板块名 → 该板块条目的 Pydantic 模型（用于回放入参校验）
_ENTRY_MODELS = {
    "timeline": TimelineEntry,
    "project": ProjectEntry,
    "skill": SkillGroup,
    "award": AwardEntry,
}


# ── 读取 ───────────────────────────────────────────────────────────────
async def get_resume(db: AsyncSession, resume_id: int, user_id: int) -> Resume | None:
    return (await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    )).scalar_one_or_none()


async def list_mine(db: AsyncSession, user_id: int) -> list[ResumeListItem]:
    rows = (await db.execute(
        select(Resume).where(Resume.user_id == user_id).order_by(Resume.updated_at.desc())
    )).scalars().all()
    return [
        ResumeListItem(id=r.id, title=r.title, lang=r.lang, template=r.template,
                       revision=r.current_revision, updatedAt=r.updated_at)
        for r in rows
    ]


async def _get_snapshot(db: AsyncSession, resume_id: int, revision: int) -> ResumeSnapshot | None:
    # 取最新一条（按 id），容忍历史可能存在的重复 (resume_id, revision) —— 不用 scalar_one_or_none 以免 500。
    return (await db.execute(
        select(ResumeSnapshot).where(
            ResumeSnapshot.resume_id == resume_id,
            ResumeSnapshot.revision == revision,
        ).order_by(ResumeSnapshot.id.desc()).limit(1)
    )).scalar_one_or_none()


def _split_snapshot_data(raw) -> dict[str, ResumeData]:
    """把快照原始 JSON 归一化为 {zh, en} 两份 ResumeData。

    兼容历史单份 ResumeData（顶层是 profile/timeline/...、无 zh 键）：视为 zh，en 置空。
    """
    if not isinstance(raw, dict):
        return {"zh": ResumeData(), "en": ResumeData()}
    if "zh" in raw or "en" in raw:
        zh = raw.get("zh") or {}
        en = raw.get("en") or {}
        return {
            "zh": ResumeData.model_validate(zh) if zh else ResumeData(),
            "en": ResumeData.model_validate(en) if en else ResumeData(),
        }
    # legacy：整份就是一份 ResumeData → 归为 zh
    return {"zh": ResumeData.model_validate(raw), "en": ResumeData()}


def _dump_both(both: dict[str, ResumeData]) -> dict:
    return {"zh": both["zh"].model_dump(mode="json"), "en": both["en"].model_dump(mode="json")}


async def get_current_data(db: AsyncSession, resume: Resume) -> ResumeData:
    """当前显示+编辑语言（resume.lang）侧的 ResumeData。"""
    snap = await _get_snapshot(db, resume.id, resume.current_revision)
    if snap is None:
        return ResumeData()
    both = _split_snapshot_data(snap.data)
    return both.get(resume.lang) or both["zh"]


async def get_both_data(db: AsyncSession, resume: Resume) -> dict[str, ResumeData]:
    snap = await _get_snapshot(db, resume.id, resume.current_revision)
    if snap is None:
        return {"zh": ResumeData(), "en": ResumeData()}
    return _split_snapshot_data(snap.data)


def to_resume_response(resume: Resume, data: ResumeData) -> ResumeResponse:
    return ResumeResponse(
        id=resume.id, title=resume.title, lang=resume.lang, template=resume.template,
        revision=resume.current_revision, data=data, updatedAt=resume.updated_at,
    )


async def read_full(db: AsyncSession, resume: Resume) -> ResumeResponse:
    return to_resume_response(resume, await get_current_data(db, resume))


# ── 写入：唯一落库函数（手动 + AI 接受共用）────────────────────────────
async def apply_and_snapshot(
    db: AsyncSession,
    resume: Resume,
    both: dict[str, ResumeData],
    summary: str,
    source: str = "manual",
) -> ResumeSnapshot:
    """落库两份语言内容。手动保存 / AI 接受都先构造好 {zh, en} 再调用。"""
    resume.current_revision += 1
    snap = ResumeSnapshot(
        resume_id=resume.id,
        revision=resume.current_revision,
        data=_dump_both(both),
        summary=(summary or "")[:160],
        source=source,
    )
    db.add(snap)
    await db.flush()
    # 刷新 resume 以载入 server_default / onupdate 生成的列（updated_at），
    # 否则后续 to_resume_response 读取 updated_at 会触发同步懒加载 → MissingGreenlet。
    await db.refresh(resume)
    return snap


async def create_resume(
    db: AsyncSession, user_id: int, title: str | None = None, lang: str = "zh",
    template: str = "pixel",
) -> Resume:
    r = Resume(user_id=user_id, title=title or "我的简历", lang=lang,
               template=template, current_revision=0)
    db.add(r)
    await db.flush()
    await apply_and_snapshot(db, r, {"zh": ResumeData(), "en": ResumeData()},
                             summary="初始创建", source="manual")
    return r


async def update_resume(
    db: AsyncSession, resume: Resume, data: ResumeData, summary: str = "手动编辑",
) -> Resume:
    """手动整体保存：只替换当前语言侧，另一侧保留。"""
    both = await get_both_data(db, resume)
    both[resume.lang] = data
    await apply_and_snapshot(db, resume, both, summary, source="manual")
    return resume


async def update_meta(
    db: AsyncSession, resume: Resume,
    lang: str | None = None, template: str | None = None,
) -> Resume:
    """切换模板 / 当前语言。直接改列，不生成快照、不前进 revision。"""
    if lang in ("zh", "en"):
        resume.lang = lang
    if template:
        resume.template = template
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume


async def delete_resume(db: AsyncSession, resume: Resume) -> None:
    await db.delete(resume)


# ── 工具回放：把一条工具调用应用到 ResumeData 副本，产出 diff ───────────
def compute_and_apply(data: ResumeData, tool: str, args: dict) -> tuple[ResumeData, dict]:
    """返回 (新 data 副本, diff)；入参非法或越界 raise ValueError/ValidationError。"""
    data = data.model_copy(deep=True)

    if tool == "update_profile":
        a = UpdateProfileArgs.model_validate(args)
        before = getattr(data.profile, a.field)
        setattr(data.profile, a.field, a.value)
        return data, {"section": "profile", "field": a.field, "index": None,
                      "before": before, "after": a.value, "deleted": False}

    if tool == "add_entry":
        a = AddEntryArgs.model_validate(args)
        model = _ENTRY_MODELS[a.section]
        validated = model.model_validate(a.entry)
        lst = getattr(data, a.section)
        lst.append(validated)
        return data, {"section": a.section, "field": None, "index": len(lst) - 1,
                      "before": None, "after": validated.model_dump(mode="json"), "deleted": False}

    if tool == "update_entry":
        a = UpdateEntryArgs.model_validate(args)
        lst = getattr(data, a.section)
        if not (0 <= a.index < len(lst)):
            raise ValueError(f"{a.section} index {a.index} 越界（当前 {len(lst)} 条）")
        before = lst[a.index].model_dump(mode="json")
        merged = {**before, **a.patch}
        new_item = _ENTRY_MODELS[a.section].model_validate(merged)
        lst[a.index] = new_item
        return data, {"section": a.section, "field": None, "index": a.index,
                      "before": before, "after": new_item.model_dump(mode="json"), "deleted": False}

    if tool == "delete_entry":
        a = DeleteEntryArgs.model_validate(args)
        lst = getattr(data, a.section)
        if not (0 <= a.index < len(lst)):
            raise ValueError(f"{a.section} index {a.index} 越界（当前 {len(lst)} 条）")
        before = lst[a.index].model_dump(mode="json")
        lst.pop(a.index)
        return data, {"section": a.section, "field": None, "index": a.index,
                      "before": before, "after": None, "deleted": True}

    raise ValueError(f"未知工具 {tool}")


def _summarize(tool: str, diff: dict) -> str:
    sec = diff.get("section", "")
    if tool == "update_profile":
        return f"修改 {sec}.{diff.get('field')}"
    if tool == "add_entry":
        return f"新增 {sec}"
    if tool == "delete_entry":
        return f"删除 {sec} #{diff.get('index')}"
    return f"更新 {sec} #{diff.get('index')}"


# ── PendingChange ──────────────────────────────────────────────────────
def to_pending_response(p: PendingChange) -> PendingChangeResponse:
    return PendingChangeResponse(
        id=p.id, groupId=p.group_id, tool=p.tool, args=p.args, diff=p.diff,
        baseRevision=p.base_revision, lang=p.lang, status=p.status, createdAt=p.created_at,
    )


async def list_pending(db: AsyncSession, resume_id: int) -> list[dict]:
    """按 group_id 聚合返回 pending 变更。"""
    rows = (await db.execute(
        select(PendingChange).where(
            PendingChange.resume_id == resume_id, PendingChange.status == "pending",
        ).order_by(PendingChange.id)
    )).scalars().all()
    groups: dict[str, dict] = {}
    for p in rows:
        g = groups.setdefault(p.group_id, {"groupId": p.group_id, "baseRevision": p.base_revision, "changes": []})
        g["changes"].append(to_pending_response(p))
    return list(groups.values())


async def list_pending_models_by_group(
    db: AsyncSession, resume_id: int, group_id: str,
) -> list[PendingChange]:
    return (await db.execute(
        select(PendingChange).where(
            PendingChange.resume_id == resume_id,
            PendingChange.group_id == group_id,
            PendingChange.status == "pending",
        ).order_by(PendingChange.id)
    )).scalars().all()


async def accept_one(db: AsyncSession, resume: Resume, pending: PendingChange) -> Resume:
    if pending.status != "pending":
        raise ResumeConflict("该变更已处理")
    if pending.base_revision != resume.current_revision:
        raise ResumeConflict(
            f"版本冲突：变更基于 r{pending.base_revision}，当前已 r{resume.current_revision}"
        )
    both = await get_both_data(db, resume)
    lang = pending.lang or resume.lang
    new_data, diff = compute_and_apply(both[lang], pending.tool, pending.args)
    both[lang] = new_data
    await apply_and_snapshot(db, resume, both, _summarize(pending.tool, diff), source="nexa")
    pending.status = "applied"
    db.add(pending)
    await _mark_others_stale(db, resume.id, exclude_id=pending.id)
    return resume


async def accept_group(db: AsyncSession, resume: Resume, group_id: str) -> Resume:
    pendings = await list_pending_models_by_group(db, resume.id, group_id)
    if not pendings:
        raise ResumeNotFound("待确认变更组不存在或已处理")
    if pendings[0].base_revision != resume.current_revision:
        raise ResumeConflict(
            f"版本冲突：变更基于 r{pendings[0].base_revision}，当前已 r{resume.current_revision}"
        )
    both = await get_both_data(db, resume)
    summaries: list[str] = []
    for p in pendings:
        lang = p.lang or resume.lang
        both[lang], diff = compute_and_apply(both[lang], p.tool, p.args)
        summaries.append(_summarize(p.tool, diff))
        p.status = "applied"
        db.add(p)
    await apply_and_snapshot(db, resume, both, "；".join(summaries)[:160], source="nexa")
    await _mark_others_stale(db, resume.id, group_ids=[group_id])
    return resume


async def deny_one(db: AsyncSession, pending: PendingChange) -> None:
    pending.status = "denied"
    db.add(pending)


async def deny_group(db: AsyncSession, resume_id: int, group_id: str) -> int:
    pendings = await list_pending_models_by_group(db, resume_id, group_id)
    for p in pendings:
        p.status = "denied"
        db.add(p)
    return len(pendings)


async def _mark_others_stale(
    db: AsyncSession,
    resume_id: int,
    *,
    exclude_id: int | None = None,
    group_ids: list[str] | None = None,
) -> None:
    """接受后，把仍 pending 的其它变更标记 denied（已过期）。

    简历版本已前进，旧 base_revision 的变更无法安全回放 → 整体作废，提示用户重新让 AI 生成。
    """
    rows = (await db.execute(
        select(PendingChange).where(
            PendingChange.resume_id == resume_id, PendingChange.status == "pending",
        )
    )).scalars().all()
    for p in rows:
        if exclude_id is not None and p.id == exclude_id:
            continue
        if group_ids and p.group_id in group_ids:
            continue
        p.status = "denied"
        db.add(p)


async def get_pending(db: AsyncSession, resume_id: int, pending_id: int) -> PendingChange | None:
    return (await db.execute(
        select(PendingChange).where(
            PendingChange.id == pending_id, PendingChange.resume_id == resume_id,
        )
    )).scalar_one_or_none()


# ── 版本 ───────────────────────────────────────────────────────────────
async def list_versions(db: AsyncSession, resume_id: int) -> list[VersionItem]:
    rows = (await db.execute(
        select(ResumeSnapshot).where(ResumeSnapshot.resume_id == resume_id)
        .order_by(ResumeSnapshot.revision.desc())
    )).scalars().all()
    return [
        VersionItem(revision=s.revision, summary=s.summary, source=s.source, createdAt=s.created_at)
        for s in rows
    ]


async def revert(db: AsyncSession, resume: Resume, target_revision: int) -> Resume:
    snap = await _get_snapshot(db, resume.id, target_revision)
    if snap is None:
        raise ResumeNotFound(f"版本 r{target_revision} 不存在")
    both = _split_snapshot_data(snap.data)
    await apply_and_snapshot(db, resume, both, summary=f"回滚到 r{target_revision}", source="manual")
    await _mark_others_stale(db, resume.id)  # 回滚后所有 pending 作废
    return resume


async def diff_versions(
    db: AsyncSession, resume_id: int, a: int, b: int,
) -> list[dict]:
    sa = await _get_snapshot(db, resume_id, a)
    sb = await _get_snapshot(db, resume_id, b)
    if sa is None or sb is None:
        raise ResumeNotFound("版本不存在")
    r = await db.get(Resume, resume_id)
    lang = r.lang if r else "zh"
    da = _split_snapshot_data(sa.data).get(lang) or ResumeData()
    db_ = _split_snapshot_data(sb.data).get(lang) or ResumeData()
    out: list[dict] = []
    sections = ("profile", "timeline", "project", "skill", "award")
    for sec in sections:
        if sec == "profile":
            before, after = da.profile.model_dump(), db_.profile.model_dump()
            changed = before != after
            out.append({"section": sec, "changed": changed,
                        "aCount": 1, "bCount": 1,
                        "fields": [k for k in before if before[k] != after[k]]})
        else:
            la, lb = getattr(da, sec), getattr(db_, sec)
            out.append({"section": sec, "changed": la != lb,
                        "aCount": len(la), "bCount": len(lb)})
    return out


# ── 对话 ───────────────────────────────────────────────────────────────
async def get_thread(db: AsyncSession, thread_id: int, user_id: int) -> ResumeChatThread | None:
    return (await db.execute(
        select(ResumeChatThread)
        .join(Resume, ResumeChatThread.resume_id == Resume.id)
        .where(ResumeChatThread.id == thread_id, Resume.user_id == user_id)
    )).scalar_one_or_none()


async def create_thread(db: AsyncSession, resume_id: int) -> ResumeChatThread:
    t = ResumeChatThread(resume_id=resume_id)
    db.add(t)
    await db.flush()
    return t


async def list_messages(db: AsyncSession, thread_id: int) -> list[ResumeChatMessage]:
    return (await db.execute(
        select(ResumeChatMessage).where(ResumeChatMessage.thread_id == thread_id)
        .order_by(ResumeChatMessage.id)
    )).scalars().all()


async def add_message(
    db: AsyncSession, thread_id: int, role: str, content: str,
) -> ResumeChatMessage:
    m = ResumeChatMessage(thread_id=thread_id, role=role, content=content)
    db.add(m)
    await db.flush()
    return m


async def history_prompt(db: AsyncSession, thread_id: int, limit: int = 8) -> str:
    """拼装最近对话为字符串，供 Agent 作为 prompt 上下文。"""
    msgs = await list_messages(db, thread_id)
    msgs = msgs[-limit:] if len(msgs) > limit else msgs
    if not msgs:
        return ""
    lines = []
    for m in msgs:
        who = "用户" if m.role == "user" else "NEXA"
        lines.append(f"{who}：{m.content}")
    return "\n".join(lines)
