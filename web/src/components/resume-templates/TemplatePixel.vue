<script setup lang="ts">
import { descLines, type TemplateProps } from './shared'

defineProps<TemplateProps>()
</script>

<template>
  <article class="qs" :class="{ 'is-print': print }" lang="zh">
    <div class="qs-banner">
      <span>◆ ADVENTURER DOSSIER ◆</span>
      <div class="qs-hp"><i /><i /><i /><i /><i /><i /><i /><i /><i class="off" /><i class="off" /></div>
    </div>

    <h1 class="qs-name">{{ data.profile.name || labels.namePh }}</h1>
    <div class="qs-title"><b>CLASS</b> {{ data.profile.title || labels.titlePh }}</div>

    <div class="qs-comms">
      <span v-if="data.profile.location"><b>◷ {{ labels.contact.location }}</b>{{ data.profile.location }}</span>
      <span v-if="data.profile.years"><b>✦ {{ labels.contact.years }}</b>{{ data.profile.years }}</span>
      <span v-if="data.profile.phone"><b>☏ {{ labels.contact.phone }}</b>{{ data.profile.phone }}</span>
      <span v-if="data.profile.email"><b>✉ {{ labels.contact.email }}</b>{{ data.profile.email }}</span>
      <span v-if="data.profile.site"><b>↗ {{ labels.contact.site }}</b>{{ data.profile.site }}</span>
      <span v-if="data.profile.github"><b>⌥ {{ labels.contact.github }}</b>{{ data.profile.github }}</span>
    </div>

    <section class="qs-panel" v-if="data.timeline.length">
      <h2><span class="g">◆</span> {{ labels.section.timeline }}</h2>
      <div>
        <div class="qs-entry" v-for="(it, i) in data.timeline" :key="'tl' + i">
          <div class="qs-q">Q.{{ String(i + 1).padStart(2, '0') }}</div>
          <div class="body">
            <div class="top">
              <div class="role">{{ it.role || '—' }}<span class="at" v-if="it.org"> · {{ it.org }}</span></div>
              <div class="date" v-if="it.date">{{ it.date }}</div>
            </div>
            <ul v-if="descLines(it.desc).length"><li v-for="(l, li) in descLines(it.desc)" :key="li">{{ l }}</li></ul>
          </div>
        </div>
      </div>
    </section>

    <section class="qs-panel" v-if="data.project.length">
      <h2><span class="g">◆</span> {{ labels.section.project }}</h2>
      <div>
        <div class="qs-entry" v-for="(it, i) in data.project" :key="'pj' + i">
          <div class="qs-q">P.{{ String(i + 1).padStart(2, '0') }}</div>
          <div class="body">
            <div class="top">
              <div class="role">{{ it.name || '—' }}<span class="at" v-if="it.stack"> · {{ it.stack }}</span></div>
            </div>
            <ul v-if="descLines(it.desc).length"><li v-for="(l, li) in descLines(it.desc)" :key="li">{{ l }}</li></ul>
          </div>
        </div>
      </div>
    </section>

    <section class="qs-panel" v-if="data.skill.length">
      <h2><span class="g">◆</span> {{ labels.section.skill }}</h2>
      <div class="qs-skills">
        <div class="row" v-for="(g, i) in data.skill" :key="'sk' + i">
          <b>{{ g.cat || '—' }}</b> · <span>{{ g.tags.join(' / ') || labels.empty }}</span>
        </div>
      </div>
    </section>

    <section class="qs-panel" v-if="data.award.length">
      <h2><span class="g">◆</span> {{ labels.section.award }}</h2>
      <div class="qs-awards">
        <div class="a" v-for="(it, i) in data.award" :key="'aw' + i">
          {{ it.name || '—' }}<span class="at" v-if="it.issuer"> · {{ it.issuer }}</span>
          <span class="yr" v-if="it.year">{{ it.year }}</span>
        </div>
      </div>
    </section>
  </article>
</template>

<style scoped>
.qs {
  background: #192043; color: #f4f4f4; border: 4px solid #3b4e7e; position: relative;
  padding: 28px 26px;
  box-shadow: 0 0 0 4px #0b0f2a, 6px 6px 0 rgba(0, 0, 0, 0.5);
  background-image: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 0, 0, 0.18) 2px, rgba(0, 0, 0, 0.18) 4px);
  /* Inter 优先，中文回退系统默认字体（已移除像素字体） */
  font-family: 'Inter', var(--font-pixel), sans-serif;
}
/* 打印/PDF：去掉悬浮光晕投影 + 各类边框（外框/角标/卷轴头条/面板框），保留深底像素本体 */
.qs.is-print { box-shadow: none; border: 0; }
.qs.is-print::before,
.qs.is-print::after { display: none; }
.qs.is-print .qs-banner { border: 0; }
.qs.is-print .qs-panel { border: 0; }
.qs::before, .qs::after { content: ''; position: absolute; width: 14px; height: 14px; border: 3px solid #73eff7; }
.qs::before { top: 8px; left: 8px; border-right: 0; border-bottom: 0; }
.qs::after { bottom: 8px; right: 8px; border-left: 0; border-top: 0; }
.qs-banner { text-align: center; font-family: 'Inter', var(--font-pixel), sans-serif; font-size: 11px; font-weight: 700;
  letter-spacing: 3px; text-transform: uppercase;
  color: #f5d976; border: 2px dashed #3b4e7e; padding: 7px; margin-bottom: 16px; text-shadow: 0 0 8px rgba(245, 217, 118, 0.4); }
.qs-hp { display: flex; gap: 3px; justify-content: center; margin-top: 6px; }
.qs-hp i { width: 13px; height: 6px; background: #38b764; display: inline-block; box-shadow: 0 0 5px rgba(56, 183, 100, 0.5); }
.qs-hp i.off { background: #2a3358; box-shadow: none; }
.qs-name { font-family: 'Inter', var(--font-pixel), sans-serif; font-size: 24px; font-weight: 700; color: #73eff7;
  text-shadow: 0 0 10px rgba(115, 239, 247, 0.45); margin: 0 0 4px; letter-spacing: 0.5px; word-break: break-word; }
.qs-title { font-family: 'JetBrains Mono', var(--font-pixel), monospace; font-size: 14px; color: #f5d976; letter-spacing: 1px; }
.qs-title b { color: #f4f4f4; }
.qs-comms { display: flex; flex-wrap: wrap; gap: 2px 12px; margin: 10px 0 4px; font-family: 'JetBrains Mono', var(--font-pixel), monospace; font-size: 13px; color: #7b8faa; }
.qs-comms span b { color: #73eff7; margin-right: 3px; }
.qs-panel { background: #223567; border: 2px solid #3b4e7e; margin-top: 12px; box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.4); }
.qs-panel > h2 { margin: 0; padding: 7px 11px; font-family: 'Inter', var(--font-pixel), sans-serif; font-size: 12px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 2px;
  color: #f5d976; border-bottom: 2px solid #3b4e7e; background: rgba(0, 0, 0, 0.18);
  display: flex; align-items: center; gap: 7px; }
.qs-panel > h2 .g { color: #73eff7; }
.qs-panel > div { padding: 7px 11px; }
.qs-entry { display: flex; gap: 9px; padding: 6px 0; border-top: 1px dashed #3b4e7e; }
.qs-entry:first-child { border-top: 0; }
.qs-q { font-family: 'JetBrains Mono', var(--font-pixel), monospace; font-size: 10px; font-weight: 500; color: #41a6f6; flex: 0 0 34px; padding-top: 2px; }
.qs-entry .body { flex: 1; min-width: 0; }
.qs-entry .top { display: flex; justify-content: space-between; gap: 10px; }
.qs-entry .role { color: #f4f4f4; font-size: 12px; }
.qs-entry .role .at { color: #7b8faa; }
.qs-entry .date { color: #f5d976; font-family: 'JetBrains Mono', var(--font-pixel), monospace; font-size: 14px; white-space: nowrap; }
.qs-entry ul { margin: 3px 0 0; padding-left: 15px; color: #a8b6d4; font-size: 11px; line-height: 1.5; }
.qs-entry li::marker { color: #38b764; }
.qs-skills { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 14px; }
.qs-skills .row { font-size: 11px; }
.qs-skills .row b { color: #73eff7; }
.qs-skills .row span { color: #a8b6d4; }
.qs-awards { display: flex; flex-direction: column; gap: 3px; }
.qs-awards .a { font-size: 11px; }
.qs-awards .a .at { color: #7b8faa; }
.qs-awards .a .yr { color: #f5d976; font-family: 'JetBrains Mono', var(--font-pixel), monospace; font-size: 14px; float: right; }
</style>
