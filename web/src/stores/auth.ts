import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, logoutServer, getMe } from '../api/auth'
import { tokenStore } from '../utils/platform'
import type { User, LoginRequest, RegisterRequest } from '../types/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!user.value)

  async function initialize() {
    const token = tokenStore.get('access_token')
    if (!token) return
    try {
      loading.value = true
      user.value = await getMe()
    } catch {
      clearTokens()
    } finally {
      loading.value = false
    }
  }

  async function login(data: LoginRequest) {
    loading.value = true
    try {
      const tokens = await apiLogin(data)
      saveTokens(tokens)
      user.value = await getMe()
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterRequest) {
    loading.value = true
    try {
      const tokens = await apiRegister(data)
      saveTokens(tokens)
      user.value = await getMe()
    } finally {
      loading.value = false
    }
  }

  /** 登出：先通知服务端吊销当前会话（best-effort），再清本地令牌。 */
  async function logout() {
    try {
      await logoutServer()
    } catch {
      /* 即使服务端调用失败也清本地 */
    }
    clearTokens()
    user.value = null
  }

  function saveTokens(tokens: { access_token: string; refresh_token: string }) {
    tokenStore.set('access_token', tokens.access_token)
    tokenStore.set('refresh_token', tokens.refresh_token)
  }

  function clearTokens() {
    tokenStore.del('access_token')
    tokenStore.del('refresh_token')
  }

  return { user, loading, isAuthenticated, initialize, login, register, logout }
})
