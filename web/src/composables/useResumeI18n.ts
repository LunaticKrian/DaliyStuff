import { computed, type Ref } from 'vue'

/** 冒险履历的中英标签集。驱动 4 套模板与编辑器面板的固定文案。 */

export interface ResumeLabels {
  namePh: string
  titlePh: string
  empty: string
  /** 板块标题：profile 概念名 + 四个 entry 板块 */
  section: {
    timeline: string
    project: string
    skill: string
    award: string
  }
  /** 联系信息标签 */
  contact: {
    location: string
    years: string
    phone: string
    email: string
    site: string
    github: string
  }
  /** 模板选择器展示名（每个模板在中/英下的叫法） */
  templates: Record<string, string>
}

const ZH: ResumeLabels = {
  namePh: '姓名',
  titlePh: '职业头衔',
  empty: '（尚未填写）',
  section: { timeline: '教育与经历', project: '项目战绩', skill: '技能', award: '荣誉与证书' },
  contact: { location: '据点', years: '资历', phone: '联络', email: '邮箱', site: '站点', github: '代码库' },
  templates: { pixel: '任务卷轴', pro: '情报档案', minimal: '远征日志', academic: '学术引文' },
}

const EN: ResumeLabels = {
  namePh: 'Name',
  titlePh: 'Title',
  empty: '(empty)',
  section: { timeline: 'Experience & Education', project: 'Projects', skill: 'Skills', award: 'Honors & Certifications' },
  contact: { location: 'Location', years: 'Experience', phone: 'Phone', email: 'Email', site: 'Site', github: 'GitHub' },
  templates: { pixel: 'Quest Scroll', pro: 'Field Report', minimal: 'Expedition Log', academic: 'Citation' },
}

export function useResumeI18n(lang: Ref<'zh' | 'en'>) {
  const labels = computed<ResumeLabels>(() => (lang.value === 'en' ? EN : ZH))
  return labels
}
