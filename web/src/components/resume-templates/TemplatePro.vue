<script setup lang="ts">
import { descLines, type TemplateProps } from './shared'

defineProps<TemplateProps>()
</script>

<template>
  <article class="fr" :class="{ 'is-print': print }" :lang="lang">
    <aside class="fr-side">
      <div class="fr-fileno">FILE NO. 0001 · CLASSIFIED</div>
      <h1 class="fr-name">{{ data.profile.name || labels.namePh }}</h1>
      <div class="fr-title">{{ data.profile.title || labels.titlePh }}</div>

      <h3>// {{ labels.contact.location }}</h3>
      <div class="fr-contact">
        <div v-if="data.profile.location"><b>{{ labels.contact.location }}</b>{{ data.profile.location }}</div>
        <div v-if="data.profile.years"><b>{{ labels.contact.years }}</b>{{ data.profile.years }}</div>
        <div v-if="data.profile.phone"><b>{{ labels.contact.phone }}</b>{{ data.profile.phone }}</div>
        <div v-if="data.profile.email"><b>{{ labels.contact.email }}</b>{{ data.profile.email }}</div>
        <div v-if="data.profile.site"><b>{{ labels.contact.site }}</b>{{ data.profile.site }}</div>
        <div v-if="data.profile.github"><b>{{ labels.contact.github }}</b>{{ data.profile.github }}</div>
        <div v-if="!data.profile.location && !data.profile.phone && !data.profile.email && !data.profile.site && !data.profile.github" class="muted">{{ labels.empty }}</div>
      </div>

      <h3 v-if="data.skill.length">// {{ labels.section.skill }}</h3>
      <div class="fr-skillrow" v-for="(g, i) in data.skill" :key="i">
        <div class="cat">{{ g.cat || '—' }}</div>
        <div class="fr-bar"><i :style="{ width: Math.min(100, 55 + g.tags.length * 9) + '%' }" /></div>
        <div class="fr-tags">{{ g.tags.join(' · ') || labels.empty }}</div>
      </div>
    </aside>

    <main class="fr-main">
      <section class="fr-sec" v-if="data.timeline.length">
        <h2><span class="n">01</span> {{ labels.section.timeline }}</h2>
        <div class="fr-item" v-for="(it, i) in data.timeline" :key="i">
          <div class="date">{{ it.date }}</div>
          <div>
            <div class="role">{{ it.role || '—' }}<span class="at" v-if="it.org"> · {{ it.org }}</span></div>
            <ul v-if="descLines(it.desc).length"><li v-for="(l, li) in descLines(it.desc)" :key="li">{{ l }}</li></ul>
          </div>
        </div>
      </section>

      <section class="fr-sec" v-if="data.project.length">
        <h2><span class="n">02</span> {{ labels.section.project }}</h2>
        <div class="fr-proj" v-for="(it, i) in data.project" :key="i">
          <div class="pn">{{ it.name || '—' }}<small v-if="it.stack">{{ it.stack }}</small></div>
          <ul v-if="descLines(it.desc).length"><li v-for="(l, li) in descLines(it.desc)" :key="li">{{ l }}</li></ul>
        </div>
      </section>

      <section class="fr-sec" v-if="data.award.length">
        <h2><span class="n">03</span> {{ labels.section.award }}</h2>
        <div class="fr-item" v-for="(it, i) in data.award" :key="i">
          <div class="date">{{ it.year }}</div>
          <div><div class="role">{{ it.name || '—' }}<span class="at" v-if="it.issuer"> · {{ it.issuer }}</span></div></div>
        </div>
      </section>
    </main>
  </article>
</template>

<style scoped>
.fr { background: #fbfaf7; color: #1d2236; font-family: 'Inter', system-ui, sans-serif;
  border: 1px solid #d9d4c7; display: grid; grid-template-columns: 32% 1fr; }
/* 打印/PDF：去外框 */
.fr.is-print { border: 0; }
.fr-side { background: #f3efe6; padding: 30px 24px; border-right: 1px solid #d9d4c7; }
.fr-main { padding: 30px 32px; }
.fr-fileno { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 2px;
  color: #b08442; border: 1px solid #b08442; display: inline-block; padding: 3px 7px; margin-bottom: 16px; }
.fr-name { font-family: 'Newsreader', Georgia, serif; font-weight: 700; font-size: 30px; margin: 0; letter-spacing: -0.5px; line-height: 1.05; }
.fr-title { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 3px;
  text-transform: uppercase; color: #284b63; margin: 6px 0 0; }
.fr-side h3 { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 2px;
  text-transform: uppercase; color: #5a6b7e; margin: 20px 0 7px; }
.fr-contact { font-family: 'JetBrains Mono', monospace; font-size: 10.5px; line-height: 1.9; color: #1d2236; }
.fr-contact div b { color: #5a6b7e; font-weight: 500; display: inline-block; width: 50px; }
.fr-contact .muted { color: #9a93a8; }
.fr-skillrow { margin: 6px 0; }
.fr-skillrow .cat { font-size: 11px; font-weight: 600; color: #284b63; }
.fr-bar { height: 4px; background: #e3ddcf; margin-top: 3px; position: relative; }
.fr-bar i { position: absolute; left: 0; top: 0; bottom: 0; background: #b08442; }
.fr-tags { font-size: 10.5px; color: #5a6b7e; margin-top: 2px; }
.fr-sec { margin-top: 22px; }
.fr-sec > h2 { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 3px;
  text-transform: uppercase; color: #1d2236; margin: 0 0 11px; padding-bottom: 5px; border-bottom: 1.5px solid #1d2236;
  display: flex; gap: 10px; align-items: baseline; }
.fr-sec > h2 .n { color: #b08442; font-weight: 600; }
.fr-item { display: grid; grid-template-columns: 88px 1fr; gap: 12px; margin-bottom: 12px; }
.fr-item .date { font-family: 'JetBrains Mono', monospace; font-size: 10.5px; color: #5a6b7e; padding-top: 2px; }
.fr-item .role { font-weight: 600; font-size: 13px; }
.fr-item .role .at { color: #5a6b7e; font-weight: 400; }
.fr-item ul { margin: 4px 0 0; padding-left: 15px; font-size: 12px; line-height: 1.55; color: #34404e; }
.fr-proj { margin-bottom: 11px; }
.fr-proj .pn { font-weight: 600; font-size: 13px; }
.fr-proj .pn small { color: #b08442; font-weight: 400; font-family: 'JetBrains Mono', monospace; font-size: 10.5px; margin-left: 6px; }
.fr-proj ul { margin: 3px 0 0; padding-left: 15px; font-size: 12px; line-height: 1.55; color: #34404e; }
</style>
