<template>
  <div class="profile-page">

    <!-- Загрузка -->
    <div v-if="loading" class="center-block">
      <div class="spinner"></div>
      <p class="hint">Загружаем профиль...</p>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="center-block">
      <div class="error-icon">⚠️</div>
      <p class="error-title">Не удалось загрузить профиль</p>
      <p class="hint">{{ error }}</p>
      <button @click="loadProfile" class="btn-primary">Попробовать снова</button>
    </div>

    <!-- Контент -->
    <div v-else-if="profile" class="profile-layout">

      <!-- Левая колонка — карточка пользователя -->
      <aside class="profile-sidebar">
        <div class="avatar-wrap">
          <div class="avatar">{{ initials }}</div>
          <div class="avatar-ring"></div>
        </div>
        <h1 class="user-name">{{ profile.name }}</h1>
        <p class="user-email">{{ profile.email }}</p>
        <p class="user-since">На сайте с {{ formattedDate }}</p>

        <div class="sidebar-stats">
          <div class="sidebar-stat">
            <span class="sidebar-stat-num">{{ profile.sessions_count }}</span>
            <span class="sidebar-stat-label">поисков</span>
          </div>
          <div class="sidebar-divider"></div>
          <div class="sidebar-stat">
            <span class="sidebar-stat-num">{{ profile.plans_count }}</span>
            <span class="sidebar-stat-label">планов</span>
          </div>
        </div>

        <button @click="goToSearch" class="btn-primary full-width">
          ＋ Новый поиск
        </button>
        <button @click="showEditForm = !showEditForm" class="btn-outline full-width">
          ✏️ Редактировать профиль
        </button>
        <button @click="handleLogout" class="btn-ghost full-width">
          Выйти
        </button>

        <!-- Форма редактирования -->
        <Transition name="slide">
          <div v-if="showEditForm" class="edit-form">
            <h3 class="edit-title">Редактировать профиль</h3>
            <div class="edit-field">
              <label>Имя</label>
              <input v-model="editName" type="text" placeholder="Ваше имя" />
            </div>
            <div class="edit-field">
              <label>Текущий пароль</label>
              <input v-model="editCurrentPassword" type="password" placeholder="Для смены пароля" />
            </div>
            <div class="edit-field">
              <label>Новый пароль <span class="optional">(необязательно)</span></label>
              <input v-model="editNewPassword" type="password" placeholder="Минимум 6 символов" />
            </div>
            <p v-if="editError" class="edit-error">{{ editError }}</p>
            <div class="edit-actions">
              <button @click="saveProfile" :disabled="editLoading" class="btn-primary">
                {{ editLoading ? 'Сохраняем...' : 'Сохранить' }}
              </button>
              <button @click="showEditForm = false" class="btn-ghost">Отмена</button>
            </div>
          </div>
        </Transition>
      </aside>

      <!-- Правая колонка — история планов -->
      <main class="profile-main">
        <div class="section-header">
          <h2 class="section-title">Мои планы обучения</h2>
          <span class="plans-count" v-if="plans.length">{{ plans.length }}</span>
        </div>

        <div v-if="plansLoading" class="plans-loading">
          <div class="spinner small"></div>
          <span>Загружаем планы...</span>
        </div>

        <div v-else-if="plans.length === 0" class="plans-empty">
          <div class="empty-icon">📋</div>
          <p class="empty-title">Планов пока нет</p>
          <p class="empty-hint">Найди вакансию и составь свой первый план обучения</p>
          <button @click="goToSearch" class="btn-primary">Начать</button>
        </div>

        <div v-else class="plans-grid">
          <div
            v-for="plan in plans"
            :key="plan.id"
            class="plan-card"
            @click="openPlan(plan.id)"
          >
            <div class="plan-card-icon">📋</div>
            <div class="plan-card-body">
              <p class="plan-card-title">{{ plan.title }}</p>
              <p class="plan-card-date">{{ formatDate(plan.created_date) }}</p>
            </div>
            <span class="plan-card-arrow">→</span>
          </div>
        </div>
      </main>
    </div>

    <!-- Модалка с планом -->
    <Transition name="fade">
      <div v-if="selectedPlan !== null" class="modal-overlay" @click.self="selectedPlan = null">
        <div class="modal">
          <div class="modal-header">
            <h2 class="modal-title">{{ selectedPlan?.plan?.title || 'План обучения' }}</h2>
            <button class="modal-close" @click="selectedPlan = null">✕</button>
          </div>

          <div v-if="planLoading" class="center-block small">
            <div class="spinner"></div>
          </div>

          <div v-else-if="selectedPlan?.plan" class="modal-body">
            <p class="modal-summary">{{ selectedPlan.plan.summary }}</p>
            <div class="modal-meta">
              <span class="meta-chip">{{ selectedPlan.plan.total_weeks || selectedPlan.plan.weeks?.length }} недель</span>
              <span class="meta-chip">{{ formatDate(selectedPlan.created_date) }}</span>
            </div>

            <div v-for="week in selectedPlan.plan.weeks" :key="week.week" class="modal-week">
              <div class="modal-week-head">
                <span class="week-badge">Неделя {{ week.week }}</span>
                <span class="week-theme">{{ week.theme }}</span>
              </div>
              <div class="modal-week-body">
                <p class="week-goal"><b>Цель:</b> {{ week.goal }}</p>
                <p class="week-tip">💡 {{ week.mentor_tip }}</p>
                <div class="week-resources">
                  <a
                    v-for="res in week.resources"
                    :key="res.url"
                    :href="res.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="res-link"
                  >
                    <span class="res-type-icon">{{ typeIcon(res.type) }}</span>
                    <span class="res-title">{{ res.title }}</span>
                    <span v-if="res.is_free" class="res-free">бесплатно</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useToastStore } from '../stores/toast'
import api from '../api/axios'

const router = useRouter()
const userStore = useUserStore()
const toast = useToastStore()

const profile = ref(null)
const loading = ref(false)
const error = ref('')
const plans = ref([])
const plansLoading = ref(false)
const selectedPlan = ref(null)
const planLoading = ref(false)

const initials = computed(() => {
  if (!profile.value?.name) return '?'
  return profile.value.name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
})

const formattedDate = computed(() => {
  if (!profile.value?.registration_date) return '—'
  return new Date(profile.value.registration_date).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric'
  })
})

const formatDate = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

const typeIcon = (type) => {
  const map = { course: '📚', video: '▶️', article: '📄', practice: '⚙️' }
  return map[type] || '🔗'
}

const loadProfile = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await api.get('/user/profile')
    profile.value = res.data
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
    const res = await api.get('/plan/history')
    plans.value = res.data.plans || []
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
    const res = await api.get(`/plan/${planId}`)
    selectedPlan.value = res.data
  } catch {
    selectedPlan.value = null
  } finally {
    planLoading.value = false
  }
}

const goToSearch = () => router.push('/search')
const handleLogout = () => { userStore.clearUser(); router.push('/login') }

// Редактирование профиля
const showEditForm = ref(false)
const editName = ref('')
const editCurrentPassword = ref('')
const editNewPassword = ref('')
const editError = ref('')
const editLoading = ref(false)

const openEdit = () => {
  editName.value = profile.value?.name || ''
  editCurrentPassword.value = ''
  editNewPassword.value = ''
  editError.value = ''
  showEditForm.value = true
}

const saveProfile = async () => {
  editError.value = ''
  if (!editName.value.trim()) { editError.value = 'Введите имя'; return }
  editLoading.value = true
  try {
    const res = await api.put('/user/profile', {
      name: editName.value.trim(),
      current_password: editCurrentPassword.value,
      new_password: editNewPassword.value
    })
    profile.value.name = res.data.name
    showEditForm.value = false
    toast.success('Профиль обновлён!')
  } catch (err) {
    editError.value = err.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    editLoading.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
/* ── Страница ── */
.profile-page {
  min-height: 80vh;
  background: #f5f5f5;
  padding: 40px 24px;
}

.center-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  gap: 16px;
  text-align: center;
}
.center-block.small { min-height: 200px; }

/* ── Спиннер ── */
.spinner {
  width: 44px; height: 44px;
  border: 4px solid #e0e0e0;
  border-top-color: #3de0cd;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.spinner.small { width: 28px; height: 28px; border-width: 3px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Ошибка ── */
.error-icon { font-size: 40px; }
.error-title { font-size: 18px; font-weight: 600; color: #e74c3c; }
.hint { font-size: 14px; color: #888; }

/* ── Layout ── */
.profile-layout {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 28px;
  align-items: start;
}

/* ── Sidebar ── */
.profile-sidebar {
  background: white;
  border-radius: 16px;
  padding: 32px 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  position: sticky;
  top: 24px;
}

.avatar-wrap {
  position: relative;
  width: 88px; height: 88px;
  margin-bottom: 4px;
}
.avatar {
  width: 88px; height: 88px;
  border-radius: 50%;
  background: linear-gradient(135deg, #7a4e30, #c09508);
  color: white;
  font-size: 28px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  position: relative; z-index: 1;
}
.avatar-ring {
  position: absolute; inset: -4px;
  border-radius: 50%;
  border: 3px solid #3de0cd;
  opacity: 0.6;
}

.user-name { font-size: 18px; font-weight: 700; color: #2d2d2d; text-align: center; }
.user-email { font-size: 13px; color: #888; text-align: center; }
.user-since { font-size: 12px; color: #bbb; text-align: center; margin-bottom: 4px; }

.sidebar-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #f9f6f3;
  border-radius: 12px;
  padding: 14px 20px;
  width: 100%;
  margin: 8px 0;
}
.sidebar-stat { display: flex; flex-direction: column; align-items: center; flex: 1; }
.sidebar-stat-num { font-size: 24px; font-weight: 700; color: #7a4e30; line-height: 1; }
.sidebar-stat-label { font-size: 11px; color: #aaa; margin-top: 2px; }
.sidebar-divider { width: 1px; height: 32px; background: #e0d8d0; }

.full-width { width: 100%; }

/* ── Кнопки ── */
.btn-primary {
  padding: 11px 20px;
  background: #3de0cd;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px; font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-primary:hover { background: #2abbaa; }

.btn-ghost {
  padding: 11px 20px;
  background: none;
  color: #7a4e30;
  border: 1.5px solid #e0d8d0;
  border-radius: 10px;
  font-size: 14px; font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-ghost:hover { border-color: #7a4e30; background: #f9f6f3; }

/* ── Main ── */
.profile-main {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
  min-height: 400px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}
.section-title { font-size: 20px; font-weight: 700; color: #2d2d2d; }
.plans-count {
  background: #7a4e30;
  color: white;
  font-size: 12px; font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
}

/* ── Загрузка планов ── */
.plans-loading {
  display: flex; align-items: center; gap: 10px;
  color: #aaa; font-size: 14px; padding: 40px 0;
  justify-content: center;
}

/* ── Пустое состояние ── */
.plans-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 60px 0; gap: 10px; text-align: center;
}
.empty-icon { font-size: 48px; }
.empty-title { font-size: 17px; font-weight: 600; color: #333; }
.empty-hint { font-size: 14px; color: #aaa; margin-bottom: 8px; }

/* ── Карточки планов ── */
.plans-grid { display: flex; flex-direction: column; gap: 10px; }

.plan-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border: 1.5px solid #f0ebe5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fdfcfb;
}
.plan-card:hover {
  border-color: #7a4e30;
  background: white;
  box-shadow: 0 4px 12px rgba(122,78,48,0.08);
  transform: translateY(-1px);
}
.plan-card-icon { font-size: 22px; flex-shrink: 0; }
.plan-card-body { flex: 1; min-width: 0; }
.plan-card-title {
  font-size: 14px; font-weight: 600; color: #2d2d2d;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.plan-card-date { font-size: 12px; color: #bbb; margin-top: 3px; }
.plan-card-arrow { color: #c09508; font-size: 18px; flex-shrink: 0; }

/* ── Модалка ── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: flex-start; justify-content: center;
  padding: 32px 20px;
  z-index: 1000;
  overflow-y: auto;
}
.modal {
  background: white;
  border-radius: 16px;
  width: 100%; max-width: 720px;
  max-height: 88vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.modal-header {
  display: flex; align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 28px 28px 0;
  position: sticky; top: 0;
  background: white;
  z-index: 1;
  border-bottom: 1px solid #f0ebe5;
  padding-bottom: 16px;
}
.modal-title { font-size: 18px; font-weight: 700; color: #7a4e30; flex: 1; }
.modal-close {
  background: none; border: none;
  font-size: 18px; cursor: pointer; color: #bbb;
  padding: 0; line-height: 1; flex-shrink: 0;
  width: auto;
}
.modal-close:hover { color: #333; }

.modal-body { padding: 20px 28px 28px; }
.modal-summary { font-size: 14px; color: #555; line-height: 1.6; margin-bottom: 12px; }
.modal-meta { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.meta-chip {
  background: #f9f6f3; color: #7a4e30;
  font-size: 12px; font-weight: 500;
  padding: 4px 12px; border-radius: 20px;
}

.modal-week {
  border: 1px solid #f0ebe5;
  border-radius: 10px;
  margin-bottom: 12px;
  overflow: hidden;
}
.modal-week-head {
  background: #f9f6f3;
  padding: 10px 16px;
  display: flex; align-items: center; gap: 10px;
}
.week-badge {
  background: #7a4e30; color: white;
  font-size: 11px; font-weight: 700;
  padding: 2px 8px; border-radius: 20px;
  white-space: nowrap;
}
.week-theme { font-size: 14px; font-weight: 600; color: #333; }

.modal-week-body { padding: 12px 16px; }
.week-goal { font-size: 13px; color: #444; margin-bottom: 6px; line-height: 1.5; }
.week-tip {
  font-size: 12px; color: #888;
  background: #fffbf0;
  border-left: 3px solid #c09508;
  padding: 6px 10px;
  border-radius: 0 6px 6px 0;
  margin-bottom: 10px;
  line-height: 1.5;
}

.week-resources { display: flex; flex-direction: column; gap: 5px; }
.res-link {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px;
  border: 1px solid #f0ebe5;
  border-radius: 7px;
  text-decoration: none;
  color: #333;
  font-size: 13px;
  transition: background 0.15s;
}
.res-link:hover { background: #f9f6f3; border-color: #3de0cd; }
.res-type-icon { font-size: 14px; flex-shrink: 0; }
.res-title { flex: 1; color: #2563eb; }
.res-free {
  background: #3de0cd22; color: #2abbaa;
  font-size: 11px; padding: 2px 7px;
  border-radius: 10px; white-space: nowrap;
}

/* ── Анимация модалки ── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ── Форма редактирования ── */
.btn-outline {
  padding: 11px 20px;
  background: none;
  color: #3de0cd;
  border: 1.5px solid #3de0cd;
  border-radius: 10px;
  font-size: 14px; font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-outline:hover { background: #3de0cd; color: white; }

.edit-form {
  margin-top: 16px;
  padding: 20px;
  background: #f9f6f3;
  border-radius: 12px;
  border: 1px solid #e0d8d0;
}
.edit-title { font-size: 15px; font-weight: 700; color: #7a4e30; margin-bottom: 14px; }
.edit-field { margin-bottom: 12px; }
.edit-field label {
  display: block; font-size: 12px;
  color: #888; margin-bottom: 4px; font-weight: 500;
}
.optional { color: #bbb; font-weight: 400; }
.edit-field input {
  width: 100%; padding: 10px 12px;
  border: 1px solid #ddd; border-radius: 8px;
  font-size: 14px; box-sizing: border-box;
  background: white;
}
.edit-field input:focus { outline: none; border-color: #7a4e30; }
.edit-error { font-size: 13px; color: #e74c3c; margin-bottom: 10px; }
.edit-actions { display: flex; gap: 10px; }
.edit-actions .btn-primary { flex: 1; }
.edit-actions .btn-ghost { flex: 1; }

.slide-enter-active, .slide-leave-active { transition: all 0.25s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-10px); }

/* ── Адаптив ── */
@media (max-width: 768px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }
  .profile-sidebar { position: static; }
  .profile-main { padding: 20px; }
  .modal { border-radius: 12px; }
  .modal-header, .modal-body { padding-left: 20px; padding-right: 20px; }
}
</style>
