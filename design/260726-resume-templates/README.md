# 冒险履历 · 4 套简历模板设计

同一份 `ResumeData`（profile / timeline / project / skill / award）+ i18n 标签（zh/en）的 4 套视觉模板。
设计语言：把「职业生涯」框成「冒险者档案」，4 套从「全 RPG 像素」到「学术出版物」递进，覆盖真实投递场景。

**设计取舍**：把所有锋芒集中在 **Quest Scroll**（招牌/签名元素），其余三套刻意克制——专业/学术简历的可读性是硬约束（招聘者、评审人要能快速扫读），所以 Pro/Minimal/Academic 不追求花哨，而靠「档案化框定」（FILE NO. / §CITATION / EXPEDITION LOG）避免沦为通用模板感。

视觉样张见 `mockup.html`（同屏 4 套，zh 标签 + 示例内容）。

---

## 共享 i18n 标签集

```
zh: {
  name_ph:"姓名", title_ph:"职业头衔",
  sections:{ timeline:"教育与经历", project:"项目战绩", skill:"技能", award:"荣誉与证书" },
  contact:{ location:"据点", phone:"联络", email:"邮箱", site:"站点", github:"代码库", years:"资历" },
  empty:"（尚未填写）"
}
en: {
  name_ph:"Name", title_ph:"Title",
  sections:{ timeline:"Experience & Education", project:"Projects", skill:"Skills", award:"Honors & Certifications" },
  contact:{ location:"Location", phone:"Phone", email:"Email", site:"Site", github:"GitHub", years:"Experience" },
  empty:"(empty)"
}
```

模板名（选择器 chip 文案）：
- `pixel` → zh「任务卷轴」/ en「Quest Scroll」
- `pro` → zh「情报档案」/ en「Field Report」
- `minimal` → zh「远征日志」/ en「Expedition Log」
- `academic` → zh「学术引文」/ en「Citation」

---

## 1. Quest Scroll（pixel）— 招牌·全 RPG 像素

- **Palette**：bg `#192043` · card `#223567` · border `#3b4e7e` · info `#73eff7` · primary `#41a6f6` · gold `#f5d976` · success `#38b764` · text `#f4f4f4`
- **Typography**：标题 `Press Start 2P`/Ark Pixel；正文 Ark Pixel；数值/坐标 `VT323` 等宽
- **Layout**：顶部「◆ ADVENTURER DOSSIER ◆」卷轴头条 + 像素 HP 条点缀；姓名作英雄字，头衔作「CLASS · LV」；联系信息成「COMMS」坐标行；各板块为带边框面板、◆ gem 标记、条目按 Q.01/Q.02 编号；scanline 叠层 + 像素转角装饰。
- **Signature**：quest-scroll 头条 + 逐条 quest log 编号 + scanline 质感。on-brand 担当。

## 2. Field Report（pro）— 干净专业·双栏

- **Palette**：paper `#fbfaf7` · ink `#1d2236` · rule `#d9d4c7` · navy `#284b63` · slate `#5a6b7e` · ochre `#b08442`（唯一强调）
- **Typography**：Newsreader（衬线，姓名/板块头）+ Inter（无衬线正文）+ JetBrains Mono（联系元数据/日期）
- **Layout**：左 sidebar ~32%（联系 mono key:value、技能为细填充 tag 条），右 main ~68%（经历、项目）。右上角 mono「FILE NO. 0001 · CLASSIFIED」标签；板块头为 small-caps mono + 前置序号「01 — EXPERIENCE」；细发丝分隔线。
- **Signature**：FIELD REPORT 文件头条 + 序号化 small-caps 板块头。招聘者友好。

## 3. Expedition Log（minimal）— 极简单栏

- **Palette**：white `#ffffff` · ink `#111111` · soft `#6b7280` · hairline `#e5e7eb` · 唯一克制强调 deep teal `#0f766e`
- **Typography**：大号 Newsreader 显示字（姓名，宽字距）+ Inter 正文 + small-caps mono 标签
- **Layout**：居中窄栏 ~640px，超大上留白；姓名超大号、下置 small-caps 头衔；联系为居中 inline 行（中点分隔）；板块以大留白 + 单根发丝线分隔。
- **Signature**：超大号姓名排版 + 细下划线强调 + small-caps 序号板块标签；极致留白纪律。编辑感单页。

## 4. Citation（academic）— 学术紧凑·编号

- **Palette**：off-white `#faf9f6` · ink `#1a1a1a` · rule `#333333` · academic blue `#1a3a5c`
- **Typography**：全程衬线（Newsreader/Source Serif），板块头 bold small-caps；JetBrains Mono 仅用于年份/页边元数据
- **Layout**：单栏紧凑；姓名居中 + 横线 + affiliation/联系行；编号板块 §1 教育 / §2 经历 / §3 项目 / §4 技能 / §5 荣誉；条目用出版物 hanging-indent 风格（左页边日期/角色，缩进正文）；奖项作编号引文列表。
- **Signature**：§编号板块标记 + 顶部 small-caps 跑栏头（「ADVENTURER DOSSIER — NAME — 2026」期刊 masthead 风）+ hanging-indent 出版物条目。学术/研究投递。

---

## 字体落地

app 当前未挂任何 Web 字体（仅本地 Ark Pixel + 系统回退）。实现时在 `web/index.html` 加 Google Fonts：
`Newsreader`（400/600/700）、`Inter`（400/500/600）、`JetBrains Mono`（400/500）。
Pixel 模板继续用 Ark Pixel / Press Start 2P / VT323（已在 app 字体栈中）。

## 组件契约（实现用）

4 个组件统一 props：`data: ResumeData; labels: ResumeLabels; lang: 'zh'|'en'`。
渲染纯展示，不编辑、不存档。空字段用 `labels.empty` 占位或不渲染该板块（Pixel 例外：保留面板框以维持质感）。
