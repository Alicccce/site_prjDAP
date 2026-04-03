import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('../pages/LoginP.vue') },
    { path: '/login', name: 'login', component: () => import('../pages/LoginP.vue') },
    { path: '/start', name: 'start', component: () => import('../pages/Start.vue') },
    { path: '/search', name: 'search', component: () => import('../pages/SearchPos.vue') },
    { path: '/skills', name: 'skills', component: () => import('../pages/Skills.vue') },
    { path: '/choice', name: 'choice', component: () => import('../pages/Frame3.vue') },
    { path: '/suggest', name: 'suggestPos', component: () => import('../pages/Frame12.vue') },
    { path: '/questions', name: 'questions', component: () => import('../pages/Questions.vue') },
    { path: '/plan', name: 'plan', component: () => import('../pages/PlanP.vue') },
    { path: '/profile', name: 'profile', component: () => import('../pages/ProfileU.vue') },
  ]
})

export default router