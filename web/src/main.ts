import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { initPlatform, setRedirector } from './utils/platform'
import { setupApiClient } from './api/client'

import './styles/theme.css'
import './styles/fonts.css'
import './styles/animations.css'
import './styles/nes-compat.css'
import './styles/mobile.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// 平台初始化必须在挂载前：加载服务器 origin 与令牌缓存（桌面端从 OS Keychain），
// 随后重建 API 客户端使 baseURL 指向配置的服务器，并接管 401 跳转为路由内跳转。
initPlatform().finally(() => {
  setupApiClient()
  setRedirector((p) => router.push(p))
  app.mount('#app')
})
