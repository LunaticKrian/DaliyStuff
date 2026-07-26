import type { Component } from 'vue'
import type { ResumeData } from '../../types/resume'
import type { ResumeLabels } from '../../composables/useResumeI18n'

/** 4 套模板统一的 props 契约 */
export interface TemplateProps {
  data: ResumeData
  labels: ResumeLabels
  lang: 'zh' | 'en'
  /** 打印/PDF 模式：模板据此关掉不适合纸张的修饰（如像素卷轴的悬浮阴影）。 */
  print?: boolean
}

/** 把 desc 文本按换行拆成要点列表（空行过滤） */
export function descLines(desc: string | undefined): string[] {
  if (!desc) return []
  return desc.split('\n').map((l) => l.trim()).filter(Boolean)
}

export interface TemplateDef {
  key: string
  /** 选择器 chip 展示名：从 labels.templates 取，由调用方解析 */
  comp: Component
}
