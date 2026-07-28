<script setup lang="ts">
import { useNotifyStore } from '../stores/notification'

const notify = useNotifyStore()

const typeConfig: Record<string, { icon: string; color: string }> = {
  success: { icon: '✓', color: 'var(--pixel-success)' },
  error: { icon: '!', color: 'var(--pixel-accent)' },
  warning: { icon: '▲', color: 'var(--pixel-warning)' },
  info: { icon: 'i', color: 'var(--pixel-info)' },
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="t in notify.toasts"
          :key="t.id"
          class="toast-item"
          :style="{ borderLeftColor: typeConfig[t.type]?.color }"
        >
          <span class="toast-icon" :style="{ color: typeConfig[t.type]?.color }">
            {{ typeConfig[t.type]?.icon }}
          </span>
          <span class="toast-msg">{{ t.message }}</span>
          <button class="toast-close" @click="notify.remove(t.id)">✕</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

.toast-container {
  --pixel-bg:#0b0d14; --pixel-bg-secondary:#14171f; --pixel-card-bg:#161924;
  --pixel-border:rgba(255,255,255,.10); --pixel-primary:#22d3ee; --pixel-accent:#fb7185;
  --pixel-warning:#fbbf24; --pixel-success:#34d399; --pixel-info:#38bdf8;
  --pixel-text:#f4f6fb; --pixel-text-secondary:#9aa3b2;
  --d-radius-sm:10px; --d-shadow:0 18px 44px -22px rgba(0,0,0,.7);
  --d-f-body:'Inter','PingFang SC',system-ui,sans-serif; --d-f-mono:'JetBrains Mono',ui-monospace,monospace;
  position: fixed; top: 76px; right: 16px; z-index: 500;
  display: flex; flex-direction: column; gap: 8px; pointer-events: none; max-width: 340px;
}
[data-theme="light"] .toast-container {
  --pixel-bg:#f4f5fa; --pixel-bg-secondary:#eef0f7; --pixel-card-bg:#ffffff;
  --pixel-border:rgba(17,20,40,.12); --pixel-primary:#0891b2; --pixel-accent:#e11d48;
  --pixel-warning:#d97706; --pixel-success:#059669; --pixel-info:#0284c7;
  --pixel-text:#0f1326; --pixel-text-secondary:#4b5568; --d-shadow:0 18px 44px -22px rgba(17,20,40,.24);
}
.toast-item {
  display: flex; align-items: center; gap: 10px;
  background: var(--pixel-card-bg); border: 1px solid var(--pixel-border);
  border-left: 3px solid var(--pixel-primary); border-radius: var(--d-radius-sm);
  padding: 11px 13px; box-shadow: var(--d-shadow); pointer-events: auto;
  font-family: var(--d-f-body); animation: toast-in .22s ease-out;
}
.toast-icon { font-family: var(--d-f-mono); font-weight: 700; font-size: 13px; flex-shrink: 0; width: 18px; text-align: center; }
.toast-msg { flex: 1; font-size: 13px; color: var(--pixel-text); line-height: 1.45; }
.toast-close { background: none; border: 0; color: var(--pixel-text-secondary); font-size: 13px; cursor: pointer; padding: 2px 4px; flex-shrink: 0; border-radius: 6px; }
.toast-close:hover { color: var(--pixel-accent); }
@keyframes toast-in { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }
.toast-enter-active { animation: toast-in .22s ease-out; }
.toast-leave-active { animation: toast-in .15s ease-in reverse; }
.toast-move { transition: transform .2s ease; }
</style>

