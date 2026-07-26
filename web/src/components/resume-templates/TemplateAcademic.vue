<script setup lang="ts">
import { descLines, type TemplateProps } from './shared'

defineProps<TemplateProps>()
</script>

<template>
  <article class="ac" :class="{ 'is-print': print }" :lang="lang">
    <div class="ac-masthead">
      <span>Adventurer Dossier</span>
      <span>{{ data.profile.name || labels.namePh }} · {{ data.profile.years || '—' }}</span>
      <span>Vol. I</span>
    </div>
    <h1 class="ac-name">{{ data.profile.name || labels.namePh }}</h1>
    <div class="ac-affil" v-if="data.profile.title || data.profile.location">
      {{ data.profile.title }}
      <template v-if="data.profile.title && data.profile.location"> · </template>
      {{ data.profile.location }}
    </div>
    <div class="ac-contact" v-if="data.profile.email || data.profile.github || data.profile.phone">
      <template v-if="data.profile.email">{{ data.profile.email }}<span>·</span></template>
      <template v-if="data.profile.github">{{ data.profile.github }}<span>·</span></template>
      <template v-if="data.profile.phone">{{ data.profile.phone }}</template>
    </div>
    <hr class="ac-sep" />

    <section class="ac-sec" v-if="data.timeline.length">
      <h2><span class="s">§1</span>{{ labels.section.timeline }}</h2>
      <div class="ac-entry" v-for="(it, i) in data.timeline" :key="i">
        <div class="meta">{{ it.date }}</div>
        <div>
          <div class="role">{{ it.role || '—' }}<span class="at" v-if="it.org"> · {{ it.org }}</span></div>
          <div class="desc" v-if="descLines(it.desc).length">{{ descLines(it.desc).join(' ') }}</div>
        </div>
      </div>
    </section>
    <hr class="ac-sep thin" v-if="data.timeline.length && data.project.length" />

    <section class="ac-sec" v-if="data.project.length">
      <h2><span class="s">§2</span>{{ labels.section.project }}</h2>
      <div class="ac-entry" v-for="(it, i) in data.project" :key="i">
        <div class="meta">{{ it.stack }}</div>
        <div>
          <div class="role">{{ it.name || '—' }}</div>
          <div class="desc" v-if="descLines(it.desc).length">{{ descLines(it.desc).join(' ') }}</div>
        </div>
      </div>
    </section>
    <hr class="ac-sep thin" v-if="data.project.length && data.skill.length" />

    <section class="ac-sec" v-if="data.skill.length">
      <h2><span class="s">§3</span>{{ labels.section.skill }}</h2>
      <div class="ac-skills">
        <template v-for="(g, i) in data.skill" :key="i">
          <b>{{ g.cat || '—' }}</b> <span>{{ g.tags.join(' · ') || labels.empty }}</span>
          <span class="sep" v-if="i < data.skill.length - 1" />
        </template>
      </div>
    </section>
    <hr class="ac-sep thin" v-if="data.skill.length && data.award.length" />

    <section class="ac-sec" v-if="data.award.length">
      <h2><span class="s">§4</span>{{ labels.section.award }}</h2>
      <div class="ac-refs">
        <div class="ac-ref" v-for="(it, i) in data.award" :key="i">
          <div class="n">[{{ i + 1 }}]</div>
          <div class="t">{{ it.name || '—' }}<span v-if="it.issuer"> · {{ it.issuer }}</span><span v-if="it.year"> ({{ it.year }})</span></div>
        </div>
      </div>
    </section>
  </article>
</template>

<style scoped>
.ac { background: #faf9f6; color: #1a1a1a; font-family: 'Newsreader', Georgia, serif; border: 1px solid #e6e3da; padding: 40px 52px; }
/* 打印/PDF：去外框 */
.ac.is-print { border: 0; }
.ac-masthead { font-family: 'JetBrains Mono', monospace; font-size: 8.5px; letter-spacing: 3px;
  text-transform: uppercase; color: #666; border-bottom: 1px solid #333; padding-bottom: 6px;
  display: flex; justify-content: space-between; gap: 8px; }
.ac-name { text-align: center; font-weight: 700; font-size: 28px; margin: 22px 0 2px; letter-spacing: 0.5px; }
.ac-affil { text-align: center; font-size: 12.5px; color: #444; }
.ac-contact { text-align: center; font-family: 'JetBrains Mono', monospace; font-size: 9.5px; color: #666; margin: 7px 0 0; }
.ac-contact span { margin: 0 6px; color: #bbb; }
.ac-sep { border: 0; border-top: 2px solid #333; margin: 16px 0; }
.ac-sep.thin { border-top: 1px solid #333; margin: 12px 0; }
.ac-sec { margin-top: 16px; }
.ac-sec > h2 { font-size: 12.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin: 0 0 9px; }
.ac-sec > h2 .s { color: #1a3a5c; font-weight: 700; margin-right: 8px; }
.ac-entry { display: grid; grid-template-columns: 100px 1fr; gap: 6px 14px; margin-bottom: 9px; font-size: 12.5px; line-height: 1.5; }
.ac-entry .meta { font-family: 'JetBrains Mono', monospace; font-size: 10.5px; color: #555; }
.ac-entry .role { font-weight: 600; }
.ac-entry .role .at { color: #555; font-weight: 400; }
.ac-entry .desc { color: #222; }
.ac-refs { font-size: 12.5px; line-height: 1.6; }
.ac-ref { display: grid; grid-template-columns: 24px 1fr; margin-bottom: 4px; }
.ac-ref .n { font-family: 'JetBrains Mono', monospace; font-size: 10.5px; color: #1a3a5c; }
.ac-ref .t span { color: #888; }
.ac-skills { font-size: 12.5px; line-height: 1.7; }
.ac-skills b { font-weight: 700; }
.ac-skills span { color: #444; }
.ac-skills .sep { display: inline-block; width: 10px; }
</style>
