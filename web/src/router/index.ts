import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { isTauri, isServerConfigured, isMobile } from '../utils/platform'

// 按平台选择视图：移动端用 views/mobile/*，桌面/Web 用 views/*。
// isMobile() 基于 UA（iOS/Android），模块加载即定，导航期取值稳定。
function pick(desktop: () => Promise<unknown>, mobile: () => Promise<unknown>) {
  return () => (isMobile() ? mobile() : desktop())
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/setup',
      name: 'setup',
      component: pick(
        () => import('../views/desktop/Setup.vue'),
        () => import('../views/mobile/Setup.vue'),
      ),
      meta: { desktop: true },
    },
    {
      path: '/desktop-settings',
      name: 'desktop-settings',
      component: () => import('../views/desktop/DesktopSettings.vue'),
      meta: { desktop: true, requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: pick(
        () => import('../views/Login.vue'),
        () => import('../views/mobile/Login.vue'),
      ),
      meta: { layout: 'auth', guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: pick(
        () => import('../views/Register.vue'),
        () => import('../views/mobile/Register.vue'),
      ),
      meta: { layout: 'auth', guest: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: pick(
        () => import('../views/Dashboard.vue'),
        () => import('../views/mobile/Dashboard.vue'),
      ),
      meta: { requiresAuth: true, tab: 'dashboard' },
    },
    {
      path: '/world-map',
      name: 'world-map',
      component: pick(
        () => import('../views/WorldMap.vue'),
        () => import('../views/mobile/WorldMap.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/items',
      name: 'items',
      component: pick(
        () => import('../views/ItemList.vue'),
        () => import('../views/mobile/Items.vue'),
      ),
      meta: { requiresAuth: true, tab: 'items' },
    },
    {
      path: '/items/new',
      name: 'item-new',
      component: pick(
        () => import('../views/ItemForm.vue'),
        () => import('../views/mobile/ItemForm.vue'),
      ),
      meta: { requiresAuth: true, tab: 'items' },
    },
    {
      path: '/items/:id',
      name: 'item-detail',
      component: pick(
        () => import('../views/ItemDetail.vue'),
        () => import('../views/mobile/ItemDetail.vue'),
      ),
      meta: { requiresAuth: true, tab: 'items' },
    },
    {
      path: '/items/:id/edit',
      name: 'item-edit',
      component: pick(
        () => import('../views/ItemForm.vue'),
        () => import('../views/mobile/ItemForm.vue'),
      ),
      meta: { requiresAuth: true, tab: 'items' },
    },
    {
      path: '/categories',
      name: 'categories',
      component: () => import('../views/Categories.vue'),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/tags',
      name: 'tags',
      component: () => import('../views/Tags.vue'),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/stats',
      name: 'stats',
      component: pick(
        () => import('../views/Stats.vue'),
        () => import('../views/mobile/Stats.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/me',
      name: 'me',
      component: pick(
        () => import('../views/Dashboard.vue'),
        () => import('../views/mobile/Profile.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: pick(
        () => import('../views/Settings.vue'),
        () => import('../views/mobile/Settings.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/quests',
      name: 'quests',
      component: pick(
        () => import('../views/Quests.vue'),
        () => import('../views/mobile/Quests.vue'),
      ),
      meta: { requiresAuth: true, tab: 'quests' },
    },
    {
      path: '/chat',
      name: 'chat',
      component: pick(
        () => import('../views/Chat.vue'),
        () => import('../views/mobile/Chat.vue'),
      ),
      meta: { requiresAuth: true, tab: 'chat' },
    },
    {
      path: '/transfer',
      name: 'transfer',
      component: pick(
        () => import('../views/Transfer.vue'),
        () => import('../views/mobile/Transfer.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/resume',
      name: 'resume',
      component: pick(
        () => import('../views/Resume.vue'),
        () => import('../views/mobile/Resume.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/character/create',
      name: 'character-create',
      component: pick(
        () => import('../views/CharacterCreation.vue'),
        () => import('../views/mobile/CharacterCreation.vue'),
      ),
      meta: { requiresAuth: true },
    },
    {
      path: '/blog',
      name: 'blog',
      component: pick(
        () => import('../views/BlogList.vue'),
        () => import('../views/mobile/BlogList.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/blog/new',
      name: 'blog-new',
      component: pick(
        () => import('../views/BlogEditor.vue'),
        () => import('../views/mobile/BlogEditor.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/blog/:id',
      name: 'blog-detail',
      component: pick(
        () => import('../views/BlogDetail.vue'),
        () => import('../views/mobile/BlogDetail.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/blog/:id/edit',
      name: 'blog-edit',
      component: pick(
        () => import('../views/BlogEditor.vue'),
        () => import('../views/mobile/BlogEditor.vue'),
      ),
      meta: { requiresAuth: true, tab: 'profile' },
    },
    {
      path: '/share/:token',
      name: 'blog-share',
      component: () => import('../views/BlogShare.vue'),
      meta: { guest: true },
    },
  ],
})

router.beforeEach(async (to) => {
  // 桌面/移动 Tauri：未配置服务器地址 → 强制走首屏接驳
  if (isTauri() && !isServerConfigured() && to.name !== 'setup') {
    return { name: 'setup' }
  }

  const auth = useAuthStore()

  if (!auth.user && !auth.loading) {
    await auth.initialize()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guest && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  // 未完成角色档案 → 强制创建
  if (auth.isAuthenticated && auth.user && !auth.user.profile_completed && to.name !== 'character-create') {
    return { name: 'character-create' }
  }
})

export default router
