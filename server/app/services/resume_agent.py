"""简历编辑 Agent：用 claude-agent-sdk 跑 GLM，通过 function call 产出「待确认变更」。

复用 task_agent 已验证的 SDK 模式：
- 字符串 prompt + system_prompt；in-process MCP 工具（@tool + create_sdk_mcp_server）。
- per-request 工具工厂，闭包绑定 resume_id / group_id / user_id。
- 工具返回 MCP 内容块：{"content":[{"type":"text","text": ...}]}。

与 task_agent 的关键区别：写工具 **不直接落库**，而是
1. 用 resume_svc.compute_and_apply 在数据副本上校验 + 算 diff（非法即返回 error 给模型重试）；
2. 写一条 PendingChange(status=pending) 入库；
3. 把 pending 信息塞进 created 列表 → 由 run_agent 即时 yield 给路由层 SSE 推送。

用户在 UI 上点「接受」才会回放工具 args 到简历并生成新版本（见 resume_svc.accept_*）。
"""
import json
import logging
import time
from collections.abc import AsyncGenerator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    StreamEvent,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)
from pydantic import ValidationError

from app.database import async_session_factory
from app.models.resume import PendingChange, Resume
from app.services import resume as resume_svc
from app.services.llm_config import (
    check_quota, load_snapshot, record_usage, sdk_env, with_extra_prompt,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
你是 PixelPack 的简历军师「NEXA」，帮助用户打磨个人简历。简历以「冒险者履历」结构存储，\
板块：profile(基本信息)、timeline(教育/工作)、project(项目)、skill(技能)、award(荣誉证书)。

可用字段：
- profile: name / title / location / years / phone / email / site / github
- timeline 每条: {type: work|edu, role, org, date, desc}
- project  每条: {name, stack, desc}
- skill    每组: {cat, tags:[...]}
- award    每条: {name, issuer, year}

规则：
1. 修改前先调用 get_section 或 get_resume 了解现状；不要凭空假设内容。
2. 只能通过工具修改简历，禁止在回复正文里输出 JSON 或简历原文。
3. 信息不足（如用户让你「补充 XX 经历」却没给细节）时，先反问，绝不编造公司/职位/年份/数字。
4. 文案改写优先：动词前置、量化成果、去套话。改 desc 时给出完整新值，不要只给片段。
5. 一次复杂指令可连续产出多个工具调用（系统会归为同一组，供用户整组确认）。
6. 全部变更产出后，用一段简洁中文说明你改了什么、为什么。

注意：变更是否生效以用户确认为准；你只是「拟变更」。
"""


def _build_tools(resume_id: int, group_id: str, created: list[dict]):
    """per-request 构造 MCP 工具，闭包绑定 resume_id / group_id。"""

    async def _current() -> tuple[Resume | None, "object"]:
        async with async_session_factory() as db:
            r = await db.get(Resume, resume_id)
            if r is None:
                return None, None
            data = await resume_svc.get_current_data(db, r)
            return r, data

    @tool(
        name="get_resume",
        description="返回当前简历的完整内容（profile/timeline/project/skill/award）。需要全局视图时调用。",
        input_schema={"type": "object", "properties": {}, "required": []},
    )
    async def get_resume(args):  # noqa: ANN001
        _, data = await _current()
        if data is None:
            return {"content": [{"type": "text", "text": json.dumps({"error": "resume not found"}, ensure_ascii=False)}]}
        return {"content": [{"type": "text", "text": json.dumps(data.model_dump(mode="json"), ensure_ascii=False)}]}

    @tool(
        name="get_section",
        description="返回简历某个板块的当前内容。section: profile|timeline|project|skill|award。",
        input_schema={
            "type": "object",
            "properties": {"section": {"type": "string", "enum": ["profile", "timeline", "project", "skill", "award"]}},
            "required": ["section"],
        },
    )
    async def get_section(args):  # noqa: ANN001
        section = (args.get("section") if isinstance(args, dict) else "") or ""
        _, data = await _current()
        if data is None:
            return {"content": [{"type": "text", "text": json.dumps({"error": "resume not found"}, ensure_ascii=False)}]}
        val = data.model_dump(mode="json").get(section)
        return {"content": [{"type": "text", "text": json.dumps({section: val}, ensure_ascii=False)}]}

    @tool(
        name="update_profile",
        description="修改 profile 的某个字段（name/title/location/years/phone/email/site/github）。value 为新值字符串。",
        input_schema={
            "type": "object",
            "properties": {
                "field": {"type": "string", "enum": ["name", "title", "location", "years", "phone", "email", "site", "github"]},
                "value": {"type": "string"},
            },
            "required": ["field", "value"],
        },
    )
    async def update_profile(args):  # noqa: ANN001
        return await _emit_change("update_profile", args, resume_id, group_id, created)

    @tool(
        name="add_entry",
        description="在某板块新增一条。section: timeline|project|skill|award；entry 为该条完整对象。",
        input_schema={
            "type": "object",
            "properties": {
                "section": {"type": "string", "enum": ["timeline", "project", "skill", "award"]},
                "entry": {"type": "object"},
            },
            "required": ["section", "entry"],
        },
    )
    async def add_entry(args):  # noqa: ANN001
        return await _emit_change("add_entry", args, resume_id, group_id, created)

    @tool(
        name="update_entry",
        description="修改某板块指定 index 的条目。patch 为要覆盖的字段（部分即可，如 {desc:'...'}）。",
        input_schema={
            "type": "object",
            "properties": {
                "section": {"type": "string", "enum": ["timeline", "project", "skill", "award"]},
                "index": {"type": "integer"},
                "patch": {"type": "object"},
            },
            "required": ["section", "index", "patch"],
        },
    )
    async def update_entry(args):  # noqa: ANN001
        return await _emit_change("update_entry", args, resume_id, group_id, created)

    @tool(
        name="delete_entry",
        description="删除某板块指定 index 的条目。",
        input_schema={
            "type": "object",
            "properties": {
                "section": {"type": "string", "enum": ["timeline", "project", "skill", "award"]},
                "index": {"type": "integer"},
            },
            "required": ["section", "index"],
        },
    )
    async def delete_entry(args):  # noqa: ANN001
        return await _emit_change("delete_entry", args, resume_id, group_id, created)

    return create_sdk_mcp_server(
        name="resumekit", version="1.0.0",
        tools=[get_resume, get_section, update_profile, add_entry, update_entry, delete_entry],
    )


async def _emit_change(tool: str, args, resume_id: int, group_id: str, created: list[dict]):
    """校验 + 算 diff + 入库 PendingChange + 推入 created 供 SSE 推送。"""
    a = args if isinstance(args, dict) else {}
    try:
        async with async_session_factory() as db:
            r = await db.get(Resume, resume_id)
            if r is None:
                return _err("resume not found")
            base_revision = r.current_revision
            lang = r.lang
            data = await resume_svc.get_current_data(db, r)
            # 校验 + 算 diff（在副本上，不落库）
            _, diff = resume_svc.compute_and_apply(data, tool, a)
            pending = PendingChange(
                resume_id=resume_id, thread_id=0, group_id=group_id,
                tool=tool, args=a, diff=diff, base_revision=base_revision,
                lang=lang, status="pending",
            )
            db.add(pending)
            await db.flush()
            pid = pending.id
            await db.commit()
        created.append({
            "pending_id": pid, "group_id": group_id, "tool": tool,
            "args": a, "diff": diff, "base_revision": base_revision, "lang": lang,
        })
        logger.info("[resume-agent·pending] id=%s tool=%s section=%s base=r%s",
                    pid, tool, diff.get("section"), base_revision)
        return {"content": [{"type": "text", "text": json.dumps(
            {"ok": True, "pending_id": pid, "tool": tool, "diff": diff}, ensure_ascii=False)}]}
    except (ValueError, ValidationError) as e:
        logger.info("[resume-agent·invalid] tool=%s err=%s", tool, e)
        return _err(f"入参非法：{e}。请检查 section/index/field 后重试。")


def _err(msg: str):
    return {"content": [{"type": "text", "text": json.dumps({"error": msg}, ensure_ascii=False)}]}


def _build_options(server, snap, lang: str = "zh") -> ClaudeAgentOptions:
    lang_label = "中文" if lang == "zh" else "English"
    base = (
        SYSTEM_PROMPT
        + f"\n\n当前简历语言：{lang_label}。所有文案改写、新增条目内容必须使用{lang_label}输出。"
    )
    return ClaudeAgentOptions(
        system_prompt=with_extra_prompt(base, snap),
        mcp_servers={"resumekit": server},
        allowed_tools=["get_resume", "get_section", "update_profile", "add_entry", "update_entry", "delete_entry"],
        permission_mode="bypassPermissions",
        max_turns=snap.max_turns,
        max_budget_usd=snap.max_budget_usd,
        env=sdk_env(snap),
        model=snap.model,
        # 开启逐 token 流式：SDK 额外产出 StreamEvent（Anthropic 原生 content_block_delta/text_delta），
        # 否则每轮只发一个完整 AssistantMessage → 前端收到的是整段而非流式。
        include_partial_messages=True,
    )


async def run_agent(
    user_id: int, resume_id: int, prompt: str, group_id: str,
) -> AsyncGenerator[dict, None]:
    """跑一次简历编辑 Agent，流式 yield 事件 dict。

    事件：
      {type: delta, text}                 助手文本增量
      {type: tool_read, name}             读取类工具调用（提示前端「读取简历中」）
      {type: tool_call, pending_id, group_id, tool, args, diff, base_revision}
      {type: done, text, subtype, count}
      {type: error, message}
    """
    # 1. per-user 配置
    async with async_session_factory() as db:
        snap = await load_snapshot(db, user_id)
    if snap is None:
        yield {"type": "error", "message": "未配置 AI 模型，请先在「设置 → AI 配置」中填写。"}
        yield {"type": "done", "text": "", "subtype": "no_config", "count": 0}
        return
    # 2. 配额校验
    async with async_session_factory() as db:
        ok, reason = await check_quota(db, user_id)
    if not ok:
        yield {"type": "error", "message": reason}
        yield {"type": "done", "text": "", "subtype": "quota_exceeded", "count": 0}
        return

    created: list[dict] = []
    # 取当前语言，注入 system_prompt，让模型用对应语言产出文案
    async with async_session_factory() as _db:
        _r = await _db.get(Resume, resume_id)
        lang = _r.lang if _r else "zh"
    server = _build_tools(resume_id, group_id, created)
    options = _build_options(server, snap, lang)

    logger.info("[resume-agent] start user=%s resume=%s model=%s turns=%s",
                user_id, resume_id, snap.model, snap.max_turns)
    full_text: list[str] = []
    seen = 0
    subtype = "unknown"
    result_msg = None
    # 当前 assistant 轮是否已通过 StreamEvent 收到逐 token 文本。
    # 用于避免与该轮完整 TextBlock 重复推送（并保留「无 partial 时的回退」）。
    turn_streamed = False
    t0 = time.monotonic()

    try:
        async for msg in query(prompt=prompt or "（开始）", options=options):
            # 逐 token 文本（include_partial_messages=True 时产出）
            if isinstance(msg, StreamEvent):
                ev = msg.event or {}
                if ev.get("type") == "content_block_delta":
                    delta = ev.get("delta") or {}
                    if delta.get("type") == "text_delta" and delta.get("text"):
                        full_text.append(delta["text"])
                        turn_streamed = True
                        yield {"type": "delta", "text": delta["text"]}
            elif isinstance(msg, AssistantMessage):
                for block in getattr(msg, "content", []) or []:
                    if isinstance(block, TextBlock) and block.text and not turn_streamed:
                        # 回退：未收到 partial 时，按整段推一次
                        full_text.append(block.text)
                        yield {"type": "delta", "text": block.text}
                    elif isinstance(block, ToolUseBlock):
                        if block.name in ("get_resume", "get_section"):
                            yield {"type": "tool_read", "name": block.name}
                turn_streamed = False  # 进入下一轮
            # 即时推送新产生的 pending（工具 handler 在两条消息之间执行）
            while len(created) > seen:
                c = created[seen]
                yield {"type": "tool_call", **c}
                seen += 1
            if isinstance(msg, ResultMessage):
                subtype = msg.subtype or "unknown"
                result_msg = msg
                logger.info("[resume-agent] done subtype=%s turns=%s", subtype, getattr(msg, "num_turns", None))
    except Exception as e:  # noqa: BLE001
        logger.exception("[resume-agent] run failed")
        yield {"type": "error", "message": f"agent 运行失败: {e}"}

    # 3. 记账
    if result_msg is not None:
        try:
            async with async_session_factory() as db:
                await record_usage(
                    db, user_id=user_id, agent_type="resume", model=snap.model,
                    result_msg=result_msg, duration_ms=int((time.monotonic() - t0) * 1000),
                )
        except Exception:
            logger.exception("[resume-agent] record_usage failed")

    yield {"type": "done", "text": "".join(full_text), "subtype": subtype, "count": len(created)}
