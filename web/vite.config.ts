import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    // 监听所有网卡：Android 模拟器经 10.0.2.2、真机经 LAN IP 才能访问到 dev server
    //（否则 Vite 默认只绑 IPv6 的 [::1]，模拟器的 IPv4 请求连不上）
    host: true,
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // WebRTC 信令走 WebSocket（/api/rtc/signal），必须开启 ws 代理，
        // 否则 vite dev 只转发普通 HTTP，WS 升级会卡 pending、到不了后端。
        ws: true,
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
