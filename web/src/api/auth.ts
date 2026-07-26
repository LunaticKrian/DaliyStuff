import { api } from './client'
import type { AuthSession, LoginRequest, ProfileUpdate, RegisterRequest, TokenResponse, User, UserUpdate, PasswordChange } from '../types/user'

export function login(data: LoginRequest) {
  return api<TokenResponse>('/auth/login', { method: 'POST', body: data })
}

export function register(data: RegisterRequest) {
  return api<TokenResponse>('/auth/register', { method: 'POST', body: data })
}

export function getMe() {
  return api<User>('/auth/me')
}

/** 登出：服务端吊销当前会话。 */
export function logoutServer() {
  return api<{ message: string }>('/auth/logout', { method: 'POST' })
}

/** 列出当前用户的活跃会话（设备）。 */
export function listSessions() {
  return api<AuthSession[]>('/auth/sessions')
}

/** 吊销指定会话（踢某设备）。 */
export function revokeSession(id: number) {
  return api<{ message: string }>(`/auth/sessions/${id}`, { method: 'DELETE' })
}

export function updateMe(data: UserUpdate) {
  return api<User>('/auth/me', { method: 'PUT', body: data })
}

export function changePassword(data: PasswordChange) {
  return api<{ message: string }>('/auth/password', { method: 'PUT', body: data })
}

export function updateProfile(data: ProfileUpdate) {
  return api<User>('/auth/profile', { method: 'PUT', body: data })
}

export function uploadPortrait(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return api<{ url: string }>('/auth/portrait', { method: 'POST', body: formData })
}
