<template>
  <div class="plan-page">
    <div class="plan-card">

      <!-- Загрузка -->
      <div v-if="loading" class="loading-block">
        <div class="loader"></div>
        <p class="loading-text">Составляем ваш план...</p>
        <p class="loading-sub">Обычно занимает 5–10 секунд</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="error-block">
        <p class="error-title">Не удалось сгенерировать план</p>
        <p class="error-text">{{ error }}</p>
        <button @click="generatePlan" class="retry-btn">Попробовать снова</button>
      </div>

      <!-- План готов -->
      <div v-else-if="plan">
        <div class="plan-header">
          <h1 class="plan-title">{{ plan.title }}</h1>
          <p class="plan-summary">{{ plan.summary }}</p>
          <div class="plan-meta">
            <span class="meta-badge">{{ totalWeeks }} недель</span>
            <span class="meta-badge">{{ jobTitle }}</span>
          </div>
        </div>

        <!-- Недели -->
        <div
          v-for="week in plan.weeks"
          :key="week.week"
          class="week-block"
        >
          <div class="week-header" @click="toggleWeek(week.week)">
            <div class="week-header-left">
              <span class="week-number">Неделя {{ week.week }}</span>
              <span class="week-theme">{{ week.theme }}</span>
            </div>
            <span class="week-toggle">{{ expandedWeeks.has(week.week) ? '▲' : '▼' }}</span>
          </div>

          <div v-if="expandedWeeks.has(week.week)" class="week-body">
            <div class="week-skills">
              <span v-for="skill in week.skills" :key="skill" class="skill-tag">{{ skill }}</span>
            </div>

            <p class="week-goal"><span class="label">Цель:</span> {{ week.goal }}</p>

            <div class="mentor-tip">
              <span class="tip-icon">💡</span>
              <p>{{ week.mentor_tip }}</p>
            </div>

            <div class="resources">
              <p class="resources-title">Материалы:</p>
              <a
                v-for="res in week.resources"
                :key="res.url"
                :href="res.url"
                target="_blank"
                rel="noopener noreferrer"
                class="resource-link"
              >
                <span class="resource-type">{{ typeLabel(res.type) }}</span>
                <span class="resource-name">{{ res.title }}</span>
                <span v-if="res.is_free" class="free-badge">бесплатно</span>
              </a>
            </div>
          </div>
        </div>

        <button @click="goBack" class="back-btn">Новый поиск</button>
      </div>

      <!-- Пустое состояние -->
      <div v-else class="empty-block">
        <p>Нет данных для генерации плана.</p>
        <button @click="$router.push('/search')" class="retry-btn">На главную</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToastStore } from '../stores/toast'
import api from '../api/axios'

const router = useRouter()
const toast = useToastStore()

const loading = ref(false)
const error = ref('')
const plan = ref(null)
const jobTitle = ref('')
const totalWeeks = ref(0)
const expandedWeeks = ref(new Set())

const typeLabel = (type) => {
  const map = { course: '📚 Курс', video: '▶️ Видео', article: '📄 Статья', practice: '⚙️ Практика' }
  return map[type] || '🔗 Ресурс'
}

const toggleWeek = (weekNum) => {
  if (expandedWeeks.value.has(weekNum)) {
    expandedWeeks.value.delete(weekNum)
  } else {
    expandedWeeks.value.add(weekNum)
  }
  expandedWeeks.value = new Set(expandedWeeks.value)
}

const generatePlan = async () => {
  error.value = ''
  plan.value = null
  loading.value = true

  try {
    const skillsRaw = localStorage.getItem('skills_answers')
    const questionsRaw = localStorage.getItem('user_questions_answers')

    if (!skillsRaw || !questionsRaw) {
      error.value = 'Не найдены данные о навыках или ответах. Пройдите шаги заново.'
      loading.value = false
      return
    }

    const skillsData = JSON.parse(skillsRaw)
    const questionsData = JSON.parse(questionsRaw)
    jobTitle.value = skillsData.jobTitle || 'Специалист'

    // Проверяем кэш
    const cacheKey = `plan_cache_${jobTitle.value}_${questionsData.level}_${questionsData.period}`
    const cached = localStorage.getItem(cacheKey)
    if (cached) {
      plan.value = JSON.parse(cached)
      totalWeeks.value = plan.value.total_weeks || plan.value.weeks?.length || 0
      if (plan.value.weeks?.length) expandedWeeks.value = new Set([1])
      loading.value = false
      toast.info('Загружен сохранённый план')
      return
    }

    const deficitSkills = []
    const allSkills = [
      ...(skillsData.mandatory || []).map(s => ({ ...s, importance: 'important' })),
      ...(skillsData.optional || []).map(s => ({ ...s, importance: 'not_important' }))
    ]
    for (const item of allSkills) {
      if (item.status === 'не знаю') {
        const skillName = item.skill || item.name
        if (!skillName) continue
        deficitSkills.push({ name: skillName, frequency: item.frequency || 0, importance: item.importance || 'not_important' })
      }
    }

    if (deficitSkills.length === 0) {
      error.value = 'Вы отметили все навыки как известные. Нечего изучать!'
      loading.value = false
      return
    }

    const response = await api.post('/plan/generate', {
      jobTitle: jobTitle.value,
      deficitSkills,
      level: questionsData.level,
      period: questionsData.period,
      timePerDay: questionsData.timePerDay,
      paymentType: questionsData.paymentType
    })

    plan.value = response.data.plan
    totalWeeks.value = plan.value.total_weeks || plan.value.weeks?.length || 0

    // Кэшируем план
    localStorage.setItem(cacheKey, JSON.stringify(plan.value))
    if (response.data.plan_id) localStorage.setItem('last_plan_id', response.data.plan_id)

    if (plan.value.weeks?.length) expandedWeeks.value = new Set([1])
    toast.success('План успешно составлен!')

  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка генерации плана. Попробуйте ещё раз.'
  } finally {
    loading.value = false
  }
}

const goBack = () => router.push('/search')

onMounted(() => { generatePlan() })
</script>

<style scoped>
.plan-page {
  min-height: 80vh;
  background-color: #f5f5f5;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.plan-card {
  max-width: 800px;
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.loading-block { text-align: center; padding: 60px 0; }
.loader {
  margin: 0 auto 20px;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #3de0cd;
  border-radius: 50%;
  width: 48px; height: 48px;
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }
.loading-text { font-size: 18px; color: #7a4e30; font-weight: 500; margin-bottom: 8px; }
.loading-sub { font-size: 14px; color: #999; }

.error-block { text-align: center; padding: 40px 0; }
.error-title { font-size: 18px; color: #e74c3c; font-weight: 600; margin-bottom: 10px; }
.error-text { font-size: 14px; color: #666; margin-bottom: 20px; }

.plan-header { margin-bottom: 28px; }
.plan-title { font-size: 22px; font-weight: 700; color: #7a4e30; margin-bottom: 10px; }
.plan-summary { font-size: 14px; color: #555; line-height: 1.6; margin-bottom: 14px; }
.plan-meta { display: flex; gap: 8px; flex-wrap: wrap; }
.meta-badge {
  background: #c0950813; color: #7a4e30;
  padding: 4px 12px; border-radius: 20px;
  font-size: 12px; font-weight: 500;
}

.week-block {
  border: 1.5px solid #eee;
  border-radius: 10px;
  margin-bottom: 12px;
  overflow: hidden;
}

.week-header {
  background: #c0950813;
  padding: 12px 16px;
  display: flex; align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}
.week-header:hover { background: #c0950820; }
.week-header-left { display: flex; align-items: center; gap: 10px; }
.week-number { font-weight: 700; color: #7a4e30; font-size: 13px; white-space: nowrap; }
.week-theme { font-size: 14px; color: #333; font-weight: 500; }
.week-toggle { color: #7a4e30; font-size: 12px; }

.week-body { padding: 16px; }

.week-skills { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.skill-tag {
  background: #3de0cd22; color: #2abbaa;
  padding: 3px 10px; border-radius: 12px;
  font-size: 12px; font-weight: 500;
}

.week-goal { font-size: 14px; color: #444; margin-bottom: 12px; line-height: 1.5; }
.label { font-weight: 600; color: #7a4e30; }

.mentor-tip {
  display: flex; gap: 10px;
  background: #fffbf0;
  border-left: 3px solid #c09508;
  padding: 10px 14px;
  border-radius: 0 8px 8px 0;
  margin-bottom: 14px;
}
.tip-icon { font-size: 16px; flex-shrink: 0; }
.mentor-tip p { font-size: 13px; color: #555; line-height: 1.5; margin: 0; }

.resources-title { font-size: 13px; font-weight: 600; color: #7a4e30; margin-bottom: 8px; }
.resource-link {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px;
  border: 1px solid #eee; border-radius: 6px;
  margin-bottom: 6px;
  text-decoration: none; color: #333; font-size: 13px;
  transition: background 0.2s;
}
.resource-link:hover { background: #f9f9f9; border-color: #3de0cd; }
.resource-type { font-size: 12px; white-space: nowrap; }
.resource-name { flex: 1; color: #2563eb; }
.free-badge {
  background: #3de0cd22; color: #2abbaa;
  padding: 2px 8px; border-radius: 10px; font-size: 11px;
}

.back-btn {
  width: 100%; padding: 13px;
  background: #7a4e30; color: white;
  border: none; border-radius: 8px;
  cursor: pointer; font-size: 15px;
  margin-top: 24px;
}
.back-btn:hover { background: #5a3b25; }

.retry-btn {
  padding: 12px 28px; background: #3de0cd;
  color: white; border: none; border-radius: 8px;
  cursor: pointer; font-size: 15px;
}
.retry-btn:hover { background: #2abbaa; }

.empty-block { text-align: center; padding: 40px 0; color: #666; }

@media (max-width: 600px) {
  .plan-card { padding: 20px; }
  .plan-title { font-size: 18px; }
  .week-header { flex-wrap: wrap; gap: 4px; }
}
</style>
