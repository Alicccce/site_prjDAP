<template>
  <div class="profile-page">
    <div class="profile-card">

      <!-- Загрузка -->
      <div v-if="loading" class="loading-block">
        <div class="loader"></div>
        <p class="loading-text">Загружаем профиль...</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="error-block">
        <p class="error-title">Не удалось загрузить профиль</p>
        <p class="error-text">{{ error }}</p>
        <button @click="loadProfile" class="retry-btn">Попробовать снова</button>
      </div>

      <!-- Профиль -->
      <div v-else-if="profile">

        <!-- Шапка -->
        <div class="profile-header">
          <div class="avatar">{{ initials }}</div>
          <div class="profile-info">
            <h1 class="profile-name">{{ profile.name }}</h1>
            <p class="profile-email">{{ profile.email }}</p>
            <p class="profile-date">На сайте с {{ formattedDate }}</p>
          </div>
        </div>

        <!-- Статистика -->
        <div class="stats-row">
          <div class="stat-card">
            <span class="stat-number">{{ profile.sessions_count }}</span>
            <span class="stat-label">Поисков</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ profile.plans_count }}</span>
            <span class="stat-label">Планов</span>
          </div>
        </div>

        <!-- История планов -->
        <div class="plans-section">
          <h2 class="section-title">История планов</h2>

          <div v-if="plansLoading" class="plans-loading">
            <div class="loader-small"></div>
            <span>Загружаем планы...</span>
          </div>

          <div v-else-if="plans.length === 0" class="plans-empty">
            <p>Планов пока нет.</p>
            <button @click="goToSearch" class="action-btn primary">Создать первый план</button>
          </div>

          <div v-else class="plans-list">
            <div
              v-for="plan in plans"
              :key="plan.id"
              class="plan-item"
              @click="openPlan(plan.id)"
            >
              <div class="plan-item-icon">📋</div>
              <div class="plan-item-info">
                <p class="plan-item-title">{{ plan.title }}</p>
                <p class="plan-item-date">{{ formatPlanDate(plan.created_date) }}</p>
              </div>
              <span class="plan-item-arrow">→</span>
            </div>
          </div>
        </div>

        <!-- Кнопки -->
        <div class="actions">
          <button @click="goToSearch" class="action-btn primary">Новый поиск</button>
          <button @click="handleLogout" class="action-btn secondary">Выйти</button>
        </div>

      </div>
    </div>

    <!-- Модалка с планом -->
    <div v-if="selectedPlan" class="modal-overlay" @click.self="selectedPlan = null">
      <div class="modal-card">
        <button class="modal-close" @click="selectedPlan = null">✕</button>

        <div v-if="planLoading" class="loading-block">
          <div class="loader"></div>
          <p class="loading-text">Загружаем план...</p>
        </div>

        <div v-else-if="selectedPlan.plan">
          <h2 class="modal-title">{{ selectedPlan.plan.title }}</h2>
          <p class="modal-summary">{{ selectedPlan.plan.summary }}</p>
          <p class="modal-meta">{{ selectedPlan.plan.total_weeks || selectedPlan.plan.weeks?.length }} недель</p>

          <div v-for="week in selectedPlan.plan.weeks" :key="week.week" class="modal-week">
            <div class="modal-week-header">
              <span class="week-num">Неделя {{ week.week }}</span>
              <span class="week-theme">{{ week.theme }}</span>
            </div>
            <p class="week-goal"><b>Цель:</b> {{ week.goal }}</p>
            <div class="week-resources">
              <a
                v-for="res in week.resources"
                :key="res.url"
                :href="res.url"
                target="_blank"
                rel="noopener noreferrer"
                class="resource-link"
              >
                {{ res.title }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import api from '../api/axios'

const router = useRouter()
const userStore = useUserStore()

const profile = ref(null)
const loading = ref(false)
const error = ref('')
const plans = ref([])
const plansLoading = ref(false)
const selectedPlan = ref(null)
const planLoading = ref(false)

const initials = computed(() => {
  if (!profile.value?.name) return '?'
  return profile.value.name
    .split(' ')
    .map(w => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
})

const formattedDate = computed(() => {
  if (!profile.value?.registration_date) return '—'
  return new Date(profile.value.registration_date).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric'
  })
})

const formatPlanDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric'
  })
}

const loadProfile = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get('/user/profile')
    profile.value = response.data
    loadPlans()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка загрузки профиля'
  } finally {
    loading.value = false
  }
}

const loadPlans = async () => {
  plansLoading.value = true
  try {
    const response = await api.get('/plan/history')
    plans.value = response.data.plans || []
  } catch {
    plans.value = []
  } finally {
    plansLoading.value = false
  }
}

const openPlan = async (planId) => {
  selectedPlan.value = {}
  planLoading.value = true
  try {
    const response = await api.get(`/plan/${planId}`)
    selectedPlan.value = response.data
  } catch {
    selectedPlan.value = null
  } finally {
    planLoading.value = false
  }
}

const goToSearch = () => router.push('/search')

const handleLogout = () => {
  userStore.clearUser()
  router.push('/login')
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  min-height: 80vh;
  background-color: #f5f5f5;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.profile-card {
  max-width: 560px;
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.loading-block { text-align: center; padding: 60px 0; }
.loader {
  margin: 0 auto 20px;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #3de0cd;
  border-radius: 50%;
  width: 40px; height: 40px;
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }
.loading-text { font-size: 16px; color: #7a4e30; }

.error-block { text-align: center; padding: 40px 0; }
.error-title { font-size: 18px; color: #e74c3c; font-weight: 600; margin-bottom: 8px; }
.error-text { font-size: 14px; color: #666; margin-bottom: 20px; }

/* Шапка профиля */
.profile-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 28px;
}
.avatar {
  width: 72px; height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #7a4e30, #5a3b25);
  color: white;
  font-size: 24px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.profile-name { font-size: 22px; font-weight: 600; color: #7a4e30; margin-bottom: 4px; }
.profile-email { font-size: 14px; color: #666; margin-bottom: 4px; }
.profile-date { font-size: 13px; color: #aaa; }

/* Статистика */
.stats-row { display: flex; gap: 16px; margin-bottom: 28px; }
.stat-card {
  flex: 1;
  background-color: #c0950813;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  display: flex; flex-direction: column; gap: 4px;
}
.stat-number { font-size: 28px; font-weight: 700; color: #7a4e30; line-height: 1; }
.stat-label { font-size: 13px; color: #888; }

/* История планов */
.plans-section { margin-bottom: 28px; }
.section-title { font-size: 17px; font-weight: 600; color: #333; margin-bottom: 14px; }

.plans-loading {
  display: flex; align-items: center; gap: 10px;
  color: #888; font-size: 14px; padding: 12px 0;
}
.loader-small {
  border: 3px solid #f0f0f0;
  border-top: 3px solid #3de0cd;
  border-radius: 50%;
  width: 20px; height: 20px;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

.plans-empty { text-align: center; padding: 20px 0; color: #888; font-size: 14px; }
.plans-empty p { margin-bottom: 14px; }

.plans-list { display: flex; flex-direction: column; gap: 8px; }
.plan-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid #eee;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.plan-item:hover { border-color: #7a4e30; background: #c0950808; }
.plan-item-icon { font-size: 20px; flex-shrink: 0; }
.plan-item-info { flex: 1; min-width: 0; }
.plan-item-title {
  font-size: 14px; font-weight: 500; color: #333;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.plan-item-date { font-size: 12px; color: #aaa; margin-top: 2px; }
.plan-item-arrow { color: #7a4e30; font-size: 16px; flex-shrink: 0; }

/* Кнопки */
.actions { display: flex; flex-direction: column; gap: 12px; }
.action-btn {
  width: 100%; padding: 13px;
  border: none; border-radius: 8px;
  font-size: 15px; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
}
.action-btn.primary { background-color: #3de0cd; color: white; }
.action-btn.primary:hover { background-color: #2abbaa; }
.action-btn.secondary { background: none; border: 1.5px solid #7a4e30; color: #7a4e30; }
.action-btn.secondary:hover { background-color: #7a4e30; color: white; }
.retry-btn {
  padding: 12px 28px; background-color: #3de0cd;
  color: white; border: none; border-radius: 8px;
  cursor: pointer; font-size: 15px;
}
.retry-btn:hover { background-color: #2abbaa; }

/* Модалка */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: flex-start; justify-content: center;
  padding: 40px 20px;
  z-index: 1000;
  overflow-y: auto;
}
.modal-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  max-width: 700px;
  width: 100%;
  position: relative;
  max-height: 85vh;
  overflow-y: auto;
}
.modal-close {
  position: absolute; top: 16px; right: 16px;
  background: none; border: none;
  font-size: 18px; cursor: pointer; color: #999;
  width: auto; padding: 4px 8px;
}
.modal-close:hover { color: #333; }
.modal-title { font-size: 20px; font-weight: 600; color: #7a4e30; margin-bottom: 10px; }
.modal-summary { font-size: 14px; color: #555; line-height: 1.6; margin-bottom: 8px; }
.modal-meta { font-size: 13px; color: #aaa; margin-bottom: 20px; }

.modal-week {
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}
.modal-week-header {
  background: #c0950813;
  padding: 10px 16px;
  display: flex; gap: 12px; align-items: center;
}
.week-num { font-weight: 700; color: #7a4e30; font-size: 13px; white-space: nowrap; }
.week-theme { font-size: 14px; color: #333; }
.week-goal { font-size: 13px; color: #555; padding: 10px 16px 6px; line-height: 1.5; }
.week-resources { padding: 0 16px 12px; display: flex; flex-direction: column; gap: 4px; }
.resource-link {
  font-size: 12px; color: #2563eb;
  text-decoration: none;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.resource-link:hover { text-decoration: underline; }

@media (max-width: 600px) {
  .profile-card { padding: 24px; }
  .profile-header { flex-direction: column; text-align: center; }
  .stats-row { flex-direction: column; }
  .modal-card { padding: 20px; }
}
</style>
