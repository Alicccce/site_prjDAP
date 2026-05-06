<template>
  <div class="plan-page">
    <div class="plan-card">

      <!-- Загрузка -->
      <div v-if="loading" class="loading-block">
        <div class="loader"></div>
        <p class="loading-text">Составляем ваш план...</p>
        <p class="loading-sub">Это займёт около 20–30 секунд</p>
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
          <div class="week-header">
            <span class="week-number">Неделя {{ week.week }}</span>
            <span class="week-theme">{{ week.theme }}</span>
          </div>

          <div class="week-body">
            <!-- Навыки недели -->
            <div class="week-skills">
              <span
                v-for="skill in week.skills"
                :key="skill"
                class="skill-tag"
              >{{ skill }}</span>
            </div>

            <!-- Цель -->
            <p class="week-goal">
              <span class="label">Цель:</span> {{ week.goal }}
            </p>

            <!-- Совет наставника -->
            <div class="mentor-tip">
              <span class="tip-icon">💡</span>
              <p>{{ week.mentor_tip }}</p>
            </div>

            <!-- Ресурсы -->
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
                <span class="resource-type" :class="res.type">{{ typeLabel(res.type) }}</span>
                <span class="resource-name">{{ res.title }}</span>
                <span v-if="res.is_free" class="free-badge">бесплатно</span>
              </a>
            </div>
          </div>
        </div>

        <!-- Кнопка сначала -->
        <button @click="goBack" class="back-btn">Начать заново</button>
      </div>

      <!-- Пустое состояние (нет данных) -->
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
import api from '../api/axios'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const plan = ref(null)
const jobTitle = ref('')
const totalWeeks = ref(0)

const typeLabel = (type) => {
  const map = { course: '📚 Курс', video: '▶️ Видео', article: '📄 Статья', practice: '⚙️ Практика' }
  return map[type] || '🔗 Ресурс'
}

const generatePlan = async () => {
  error.value = ''
  plan.value = null
  loading.value = true

  try {
    // Берём навыки из localStorage (Skills.vue сохраняет их)
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

    // Собираем навыки которые пользователь НЕ знает
    const deficitSkills = []

    const allSkills = [
      ...(skillsData.mandatory || []).map(s => ({ ...s, importance: 'important' })),
      ...(skillsData.optional || []).map(s => ({ ...s, importance: 'not_important' }))
    ]

    for (const item of allSkills) {
      if (item.status === 'не знаю') {
        // item.skill — название навыка (строка)
        // item.frequency — частота (число, может отсутствовать в старых данных)
        const skillName = item.skill || item.name
        if (!skillName) continue
        deficitSkills.push({
          name: skillName,
          frequency: item.frequency || 0,
          importance: item.importance || 'not_important'
        })
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

  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка генерации плана. Попробуйте ещё раз.'
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/search')
}

onMounted(() => {
  generatePlan()
})
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
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Загрузка */
.loading-block {
  text-align: center;
  padding: 60px 0;
}

.loader {
  margin: 0 auto 20px;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #3de0cd;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 18px;
  color: #7a4e30;
  font-weight: 500;
  margin-bottom: 8px;
}

.loading-sub {
  font-size: 14px;
  color: #999;
}

/* Ошибка */
.error-block {
  text-align: center;
  padding: 40px 0;
}

.error-title {
  font-size: 18px;
  color: #e74c3c;
  font-weight: 600;
  margin-bottom: 10px;
}

.error-text {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
}

/* Заголовок плана */
.plan-header {
  margin-bottom: 32px;
  text-align: center;
}

.plan-title {
  font-size: 24px;
  font-weight: 600;
  color: #7a4e30;
  margin-bottom: 12px;
  -webkit-text-stroke: 0.5px #7a4e30;
}

.plan-summary {
  font-size: 15px;
  color: #555;
  line-height: 1.6;
  margin-bottom: 16px;
}

.plan-meta {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.meta-badge {
  background-color: #c0950813;
  color: #7a4e30;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

/* Блок недели */
.week-block {
  border: 1px solid #eee;
  border-radius: 10px;
  margin-bottom: 20px;
  overflow: hidden;
}

.week-header {
  background-color: #c0950813;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.week-number {
  font-weight: 700;
  color: #7a4e30;
  font-size: 14px;
  white-space: nowrap;
}

.week-theme {
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.week-body {
  padding: 16px 20px;
}

/* Теги навыков */
.week-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.skill-tag {
  background-color: #3de0cd22;
  color: #2abbaa;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* Цель */
.week-goal {
  font-size: 14px;
  color: #444;
  margin-bottom: 12px;
  line-height: 1.5;
}

.label {
  font-weight: 600;
  color: #7a4e30;
}

/* Совет наставника */
.mentor-tip {
  display: flex;
  gap: 10px;
  background-color: #fffbf0;
  border-left: 3px solid #d4c53d;
  padding: 10px 14px;
  border-radius: 0 8px 8px 0;
  margin-bottom: 14px;
}

.tip-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.mentor-tip p {
  font-size: 13px;
  color: #555;
  line-height: 1.5;
  margin: 0;
}

/* Ресурсы */
.resources-title {
  font-size: 13px;
  font-weight: 600;
  color: #7a4e30;
  margin-bottom: 8px;
}

.resource-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 6px;
  text-decoration: none;
  color: #333;
  font-size: 13px;
  transition: background 0.2s;
}

.resource-link:hover {
  background-color: #f9f9f9;
  border-color: #3de0cd;
}

.resource-type {
  font-size: 12px;
  white-space: nowrap;
}

.resource-name {
  flex: 1;
  color: #2563eb;
}

.free-badge {
  background-color: #3de0cd22;
  color: #2abbaa;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  white-space: nowrap;
}

/* Кнопки */
.retry-btn {
  padding: 12px 28px;
  background-color: #3de0cd;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  margin-top: 10px;
}

.retry-btn:hover {
  background-color: #2abbaa;
}

.back-btn {
  width: 100%;
  padding: 14px;
  background-color: #7a4e30;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 24px;
}

.back-btn:hover {
  background-color: #5a3b25;
}

.empty-block {
  text-align: center;
  padding: 40px 0;
  color: #666;
}

@media (max-width: 600px) {
  .plan-card {
    padding: 20px;
  }

  .plan-title {
    font-size: 20px;
  }

  .week-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
