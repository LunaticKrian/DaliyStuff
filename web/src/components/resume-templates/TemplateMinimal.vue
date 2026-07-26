<script setup lang="ts">
import type { TemplateProps } from './shared'

defineProps<TemplateProps>()
</script>

<template>
  <article class="el" :class="{ 'is-print': print }" :lang="lang">
    <div class="el-wrap">
      <h1 class="el-name">{{ data.profile.name || labels.namePh }}</h1>
      <div class="el-underline" />
      <div class="el-title">{{ data.profile.title || labels.titlePh }}</div>

      <div class="el-contact" v-if="data.profile.location || data.profile.years || data.profile.email || data.profile.github">
        <template v-if="data.profile.location">{{ data.profile.location }}<span>·</span></template>
        <template v-if="data.profile.years">{{ data.profile.years }}<span>·</span></template>
        <template v-if="data.profile.email">{{ data.profile.email }}<span>·</span></template>
        <template v-if="data.profile.github">{{ data.profile.github }}</template>
      </div>

      <section class="el-sec" v-if="data.timeline.length">
        <h2><span class="n">01</span> {{ labels.section.timeline }}</h2>
        <hr class="el-rule" />
        <div class="el-item" v-for="(it, i) in data.timeline" :key="i">
          <div class="top">
            <div class="role">{{ it.role || '—' }}<span class="at" v-if="it.org"> · {{ it.org }}</span></div>
            <div class="date" v-if="it.date">{{ it.date }}</div>
          </div>
          <p v-if="it.desc">{{ it.desc }}</p>
        </div>
      </section>

      <section class="el-sec" v-if="data.project.length">
        <h2><span class="n">02</span> {{ labels.section.project }}</h2>
        <hr class="el-rule" />
        <div class="el-item" v-for="(it, i) in data.project" :key="i">
          <div class="top">
            <div class="role">{{ it.name || '—' }}<span class="at" v-if="it.stack"> · {{ it.stack }}</span></div>
          </div>
          <p v-if="it.desc">{{ it.desc }}</p>
        </div>
      </section>

      <section class="el-sec" v-if="data.skill.length">
        <h2><span class="n">03</span> {{ labels.section.skill }}</h2>
        <hr class="el-rule" />
        <div class="el-skills">
          <template v-for="(g, i) in data.skill" :key="i">
            <b>{{ g.cat || '—' }}</b> — <span>{{ g.tags.join(' · ') || labels.empty }}</span>
            <span class="sep" v-if="i < data.skill.length - 1" />
          </template>
        </div>
      </section>

      <section class="el-sec" v-if="data.award.length">
        <h2><span class="n">04</span> {{ labels.section.award }}</h2>
        <hr class="el-rule" />
        <div class="el-item" v-for="(it, i) in data.award" :key="i">
          <div class="top">
            <div class="role">{{ it.name || '—' }}<span class="at" v-if="it.issuer"> · {{ it.issuer }}</span></div>
            <div class="date" v-if="it.year">{{ it.year }}</div>
          </div>
        </div>
      </section>
    </div>
  </article>
</template>

<style scoped>
.el { background: #fff; color: #111; font-family: 'Inter', system-ui, sans-serif; padding: 56px 48px; border: 1px solid #e5e7eb; }
/* 打印/PDF：去外框 */
.el.is-print { border: 0; }
.el-wrap { max-width: 580px; margin: 0 auto; }
.el-name { font-family: 'Newsreader', Georgia, serif; font-weight: 600; font-size: 46px; line-height: 1; margin: 0; letter-spacing: -1px; word-break: break-word; }
.el-underline { width: 48px; height: 3px; background: #0f766e; margin: 16px 0 12px; }
.el-title { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: #6b7280; }
.el-contact { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #6b7280; margin: 18px 0 0; letter-spacing: 0.5px; }
.el-contact span { margin: 0 7px; color: #d1d5db; }
.el-sec { margin-top: 40px; }
.el-sec > h2 { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 3px;
  text-transform: uppercase; color: #111; margin: 0 0 4px; display: flex; gap: 10px; align-items: baseline; }
.el-sec > h2 .n { color: #0f766e; }
.el-rule { border: 0; border-top: 1px solid #e5e7eb; margin: 6px 0 16px; }
.el-item { margin-bottom: 18px; }
.el-item .top { display: flex; justify-content: space-between; align-items: baseline; gap: 14px; }
.el-item .role { font-family: 'Newsreader', Georgia, serif; font-size: 17px; font-weight: 600; }
.el-item .role .at { color: #6b7280; font-weight: 400; font-size: 14px; }
.el-item .date { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #9ca3af; white-space: nowrap; }
.el-item p { margin: 5px 0 0; font-size: 12.5px; line-height: 1.65; color: #374151; }
.el-skills { font-size: 12.5px; line-height: 1.9; color: #374151; }
.el-skills b { color: #111; font-weight: 600; }
.el-skills .sep { display: inline-block; width: 10px; }
</style>
