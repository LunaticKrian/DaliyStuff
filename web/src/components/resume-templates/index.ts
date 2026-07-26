import type { TemplateDef } from './shared'
import TemplatePixel from './TemplatePixel.vue'
import TemplatePro from './TemplatePro.vue'
import TemplateMinimal from './TemplateMinimal.vue'
import TemplateAcademic from './TemplateAcademic.vue'

/** 4 套模板注册表。key 与后端 Resume.template 取值一致。 */
export const TEMPLATE_DEFS: TemplateDef[] = [
  { key: 'pixel', comp: TemplatePixel },
  { key: 'pro', comp: TemplatePro },
  { key: 'minimal', comp: TemplateMinimal },
  { key: 'academic', comp: TemplateAcademic },
]

export const DEFAULT_TEMPLATE = 'pixel'

export function templateComponent(key: string) {
  return (TEMPLATE_DEFS.find((t) => t.key === key) ?? TEMPLATE_DEFS[0]).comp
}

export { type TemplateProps, descLines } from './shared'
