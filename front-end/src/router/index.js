import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('../pages/LoginP.vue') },
    { path: '/login', name: 'login', component: () => import('../pages/LoginP.vue') },
    { path: '/start', name: 'start', component: () => import('../pages/Start.vue'), meta: { requiresAuth: true } },
    { path: '/search', name: 'search', component: () => import('../pages/SearchPos.vue'), meta: { requiresAuth: true } },
    { path: '/skills', name: 'skills', component: () => import('../pages/Skills.vue'), meta: { requiresAuth: true } },
    { path: '/choice', name: 'choice', component: () => import('../pages/Frame3.vue'), meta: { requiresAuth: true } },
    { path: '/suggest', name: 'suggestPos', component: () => import('../pages/Frame12.vue'), meta: { requiresAuth: true } },
    { path: '/questions', name: 'questions', component: () => import('../pages/Questions.vue'), meta: { requiresAuth: true } },
    { path: '/plan', name: 'plan', component: () => import('../pages/PlanP.vue'), meta: { requiresAuth: true } },
    { path: '/profile', name: 'profile', component: () => import('../pages/ProfileU.vue'), meta: { requiresAuth: true } },
  ]
})

// Защита роутов — редирект на /login если нет токена
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next({ name: 'login' })
  } else if ((to.name === 'login' || to.name === 'home') && token) {
    next({ name: 'start' })
  } else {
    next()
  }
})

export default router