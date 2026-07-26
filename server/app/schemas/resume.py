"""冒险者履历 DOSSIER · Pydantic 模型。

- ResumeData：简历内容结构（== ResumeSnapshot.data），同时用于工具入参校验。
- 工具入参：ToolArg 校验；越界 index / 非法 section / 非法 field 在 service 层 raise。
- API 响应：camelCase，与前端 types/resume.ts 严格一致。
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

TimelineType = Literal["work", "edu"]
SectionName = Literal["timeline", "project", "skill", "award"]
ProfileField = Literal["name", "title", "location", "years", "phone", "email", "site", "github"]


# ── 简历内容 ────────────────────────────────────────────────────────────
class ProfileData(BaseModel):
    name: str = ""
    title: str = ""
    location: str = ""
    years: str = ""
    phone: str = ""
    email: str = ""
    site: str = ""
    github: str = ""


class TimelineEntry(BaseModel):
    type: TimelineType = "work"
    role: str = ""
    org: str = ""
    date: str = ""
    desc: str = ""


class ProjectEntry(BaseModel):
    name: str = ""
    stack: str = ""
    desc: str = ""


class SkillGroup(BaseModel):
    cat: str = ""
    tags: list[str] = Field(default_factory=list)


class AwardEntry(BaseModel):
    name: str = ""
    issuer: str = ""
    year: str = ""


class ResumeData(BaseModel):
    profile: ProfileData = Field(default_factory=ProfileData)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    project: list[ProjectEntry] = Field(default_factory=list)
    skill: list[SkillGroup] = Field(default_factory=list)
    award: list[AwardEntry] = Field(default_factory=list)


# ── 工具入参（Agent 写工具）── 用于在 service 层校验 + 回放 ──────────────
class UpdateProfileArgs(BaseModel):
    field: ProfileField
    value: str


class AddEntryArgs(BaseModel):
    section: SectionName
    entry: dict[str, Any]


class UpdateEntryArgs(BaseModel):
    section: SectionName
    index: int
    patch: dict[str, Any]


class DeleteEntryArgs(BaseModel):
    section: SectionName
    index: int


# ── API 请求 ────────────────────────────────────────────────────────────
RESUME_TEMPLATES = ("pixel", "pro", "minimal", "academic")


class ResumeCreate(BaseModel):
    title: str | None = Field(None, max_length=120)
    lang: Literal["zh", "en"] = "zh"
    template: str = "pixel"


class ResumeUpdate(BaseModel):
    """整体手动保存。可选 summary 记录本次变更一句话。data 为当前语言侧内容。"""
    data: ResumeData
    summary: str = Field("手动编辑", max_length=160)


class ResumeMetaUpdate(BaseModel):
    """轻量更新：切换模板 / 当前语言。不生成快照、不前进 revision。"""
    lang: Literal["zh", "en"] | None = None
    template: str | None = None


class ThreadCreate(BaseModel):
    pass


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class InlinePolishRequest(BaseModel):
    """字段内联润色。section=index 处的某字段，按 instruction 重写，产出一条 pending。"""
    section: Literal["profile", "timeline", "project", "skill", "award"]
    index: int = 0          # profile 视为单一对象，index 固定 0
    field: str | None = None  # profile / 文案字段名；None 表示改整条
    instruction: str = Field(..., min_length=1, max_length=500)


# ── API 响应（camelCase，前端一致）──────────────────────────────────────
# 注：ORM 列为 snake_case（group_id/base_revision/created_at/current_revision），
# 与响应的 camelCase 字段不对应，故不用 from_attributes，由 service 层 to_response() 构造。
class ResumeResponse(BaseModel):
    id: int
    title: str
    lang: str
    template: str
    revision: int
    data: ResumeData
    updatedAt: datetime


class ResumeListItem(BaseModel):
    id: int
    title: str
    lang: str
    template: str
    revision: int
    updatedAt: datetime


class DiffPayload(BaseModel):
    """PendingChange.diff 的结构，供前端渲染「旧→新」。"""
    section: str
    field: str | None = None
    index: int | None = None
    before: Any = None
    after: Any = None
    deleted: bool = False


class PendingChangeResponse(BaseModel):
    id: int
    groupId: str
    tool: str
    args: dict[str, Any]
    diff: dict[str, Any]
    baseRevision: int
    lang: str
    status: str
    createdAt: datetime


class PendingGroup(BaseModel):
    """按 group_id 聚合的待确认变更。"""
    groupId: str
    baseRevision: int
    changes: list[PendingChangeResponse]


class VersionItem(BaseModel):
    revision: int
    summary: str
    source: str
    createdAt: datetime


class VersionDiff(BaseModel):
    """两个版本的粗粒度差异：按 section 列出 changed 项。"""
    a: int
    b: int
    sections: list[dict[str, Any]]


class InlinePolishResponse(BaseModel):
    pending: PendingChangeResponse
