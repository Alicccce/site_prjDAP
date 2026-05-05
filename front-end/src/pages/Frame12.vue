<template>
  <div class="suggest-page">
    <div class="suggest-card">

      <div v-if="loading" class="loading-block">
        <div class="loader"></div>
        <p class="loading-text">Ищем подходящие должности на HH.ru...</p>
        <p class="loading-sub">Анализируем вакансии и сопоставляем с вашими навыками</p>
      </div>

      <div v-else-if="error" class="error-block">
        <p class="error-title">Не удалось загрузить должности</p>
        <p class="error-text">{{ error }}</p>
        <div class="error-actions">
          <button @click="loadPositions" class="retry-btn">Попробовать снова</button>
          <button @click="$router.push('/choice')" class="back-link">← Изменить фильтры</button>
        </div>
      </div>

      <div v-else-if="positions.length > 0">
        <div class="page-header">
          <h1 class="page-title">Подходящие должности</h1>
          <p class="page-subtitle">На основе ваших навыков ({{ userSkillsCount }}) мы подобрали {{ positions.length }} варианта</p>
        </div>

        <div class="positions-list">
          <div v-for="(pos, idx) in positions" :key="idx" :class="['position-card', { selected: selectedIdx === idx }]">
            <div class="card-header">
              <div class="card-title-row">
                <h2 class="position-title">{{ pos.title }}</h2>
                <span class="match-badge" :class="matchClass(pos.match_score)">{{ pos.match_score }}% совпадение</span>
              </div>
              <p class="vacancies-count">{{ pos.total_vacancies ? pos.total_vacancies.toLocaleString() + ' вакансий на HH.ru' : '' }}</p>
            </div>

            <div v-if="pos.match_skills && pos.match_skills.length > 0" class="skills-section">
              <p class="skills-label">✅ Ваши навыки подходят:</p>
              <div class="skills-chips">
                <span v-for="skill in pos.match_skills" :key="skill" class="skill-chip match">{{ skill }}</span>
              </div>
            </div>

            <div v-if="pos.new_skills && pos.new_skills.length > 0" class="skills-section">
              <p class="skills-label">📚 Нужно изучить (топ {{ pos.new_skills.length }}):</p>
              <div class="skills-chips">
                <span v-for="skill in pos.new_skills" :key="skill" class="skill-chip new">{{ skill }}</span>
              </div>
            </div>

            <button v-if="selectedIdx !== idx" @click="selectPosition(pos, idx)" class="select-btn">
              Выбрать эту должность
            </button>
            <div v-else class="selected-indicator">
              <span>✓</span> Выбрано
            </div>
          </div>
        </div>

        <div class="continue-area">
          <button @click="continueToQuestions" :disabled="selectedIdx === null" class="continue-btn">
            {{ selectedIdx !== null ? 'Продолжить →' : 'Выберите должность' }}
          </button>
          <button @click="$router.push('/choice')" class="back-link">← Изменить фильтры</button>
        </div>
      </div>

      <div v-else class="empty-block">
        <p class="empty-title">Должности не найдены</p>
        <p class="empty-text">Попробуйте изменить фильтры или добавить больше навыков</p>
        <button @click="$router.push('/choice')" class="retry-btn">← Изменить фильтры</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useBranch2Store } from '../stores/branch2'

const router = useRouter()
const store = useBranch2Store()

const positions = ref([])
const loading = ref(false)
const error = ref('')
const selectedIdx = ref(null)

const userSkillsCount = computed(() => store.userSkills.length)

const matchClass = (score) => {
  if (score >= 60) return 'high'
  if (score >= 30) return 'medium'
  return 'low'
}

const loadPositions = async () => {
  if (store.userSkills.length === 0 && !store.filters.specialization) {
    router.push('/choice')
    return
  }
  loading.value = true
  error.value = ''
  selectedIdx.value = null
  try {
    await store.fetchSuggestedPositions()
    positions.value = store.suggestedPositions
  } catch (e) {
    error.value = store.error || 'Ошибка загрузки должностей'
  } finally {
    loading.value = false
  }
}

const selectPosition = (pos, idx) => {
  selectedIdx.value = idx
  store.selectPosition(pos)
}

const continueToQuestions = () => {
  if (selectedIdx.value === null) return
  router.push('/questions')
}

onMounted(() => { loadPositions() })
</script>

<style scoped>
.suggest-page { min-height: 80vh; background-color: #f5f5f5; padding: 40px 20px; display: flex; justify-content: center; align-items: flex-start; }
.suggest-card { max-width: 800px; width: 100%; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.loading-block { text-align: center; padding: 60px 0; }
.loader { margin: 0 auto 20px; border: 4px solid #f0f0f0; border-top: 4px solid #3de0cd; border-radius: 50%; width: 48px; height: 48px; animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.loading-text { font-size: 18px; color: #7a4e30; font-weight: 500; margin-bottom: 8px; }
.loading-sub { font-size: 14px; color: #999; }
.error-block { text-align: center; padding: 40px 0; }
.error-title { font-size: 18px; color: #e74c3c; font-weight: 600; margin-bottom: 10px; }
.error-text { font-size: 14px; color: #666; margin-bottom: 20px; }
.error-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.page-header { margin-bottom: 28px; text-align: center; }
.page-title { font-size: 26px; font-weight: 600; color: #7a4e30; margin-bottom: 8px; }
.page-subtitle { font-size: 14px; color: #888; }
.positions-list { display: flex; flex-direction: column; gap: 20px; margin-bottom: 28px; }
.position-card { border: 2px solid #eee; border-radius: 12px; padding: 24px; transition: all 0.2s; }
.position-card:hover { border-color: #7a4e30; box-shadow: 0 4px 12px rgba(122,78,48,0.1); }
.position-card.selected { border-color: #3de0cd; background: #f0fffe; }
.card-header { margin-bottom: 16px; }
.card-title-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 4px; }
.position-title { font-size: 20px; font-weight: 600; color: #333; margin: 0; }
.match-badge { padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; white-space: nowrap; }
.match-badge.high { background: #d4edda; color: #155724; }
.match-badge.medium { background: #fff3cd; color: #856404; }
.match-badge.low { background: #f8d7da; color: #721c24; }
.vacancies-count { font-size: 13px; color: #999; margin: 0; }
.skills-section { margin-bottom: 14px; }
.skills-label { font-size: 13px; font-weight: 500; color: #555; margin-bottom: 8px; }
.skills-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.skill-chip { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.skill-chip.match { background: #3de0cd22; color: #2abbaa; }
.skill-chip.new { background: #c0950813; color: #7a4e30; }
.select-btn { width: 100%; padding: 10px; background: #7a4e30; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; margin-top: 8px; }
.select-btn:hover { background: #5a3b25; }
.selected-indicator { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 10px; background: #3de0cd22; color: #2abbaa; border-radius: 8px; font-size: 14px; font-weight: 600; margin-top: 8px; }
.continue-area { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.continue-btn { width: 100%; padding: 14px; background: #3de0cd; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 500; cursor: pointer; }
.continue-btn:hover:not(:disabled) { background: #2abbaa; }
.continue-btn:disabled { background: #ccc; cursor: not-allowed; }
.back-link { background: none; border: none; color: #7a4e30; font-size: 14px; cursor: pointer; padding: 4px 8px; width: auto; margin: 0; text-decoration: underline; }
.empty-block { text-align: center; padding: 40px 0; }
.empty-title { font-size: 18px; color: #333; font-weight: 600; margin-bottom: 8px; }
.empty-text { font-size: 14px; color: #666; margin-bottom: 20px; }
.retry-btn { padding: 12px 28px; background: #3de0cd; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 15px; width: auto; margin: 0; }
.retry-btn:hover { background: #2abbaa; }
</style>
