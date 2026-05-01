<template>
  <div class="vacancy-page">
    <div class="vacancy-card">
      <h1 class="vacancy-title">Должность: {{ analysisData.jobTitle }}</h1>
      <button @click="resetSkills" class="reset-btn-small">Сбросить</button>

      <!-- Обязательные навыки -->
      <div v-if="mandatorySkills.length" class="skills-section">
        <h2 class="section-title mandatory">Обязательные навыки:</h2>
        <div class="skills-table">
          <div class="skills-header">
            <span>Навык</span>
            <span>Владею</span>
            <span>Не знаю</span>
          </div>
          <div v-for="(skill, index) in mandatorySkills" :key="index" class="skills-row">
            <span class="skill-name">{{ skill }}</span>
            <div class="checkbox-cell">
              <input type="radio" :name="'mandatory-' + index" value="know" v-model="mandatoryStatus[index]" />
            </div>
            <div class="checkbox-cell">
              <input type="radio" :name="'mandatory-' + index" value="dontknow" v-model="mandatoryStatus[index]" />
            </div>
          </div>
        </div>
      </div>

      <!-- Необязательные навыки -->
      <div v-if="optionalSkills.length" class="skills-section">
        <h2 class="section-title optional">Необязательные навыки, но полезные в собеседовании:</h2>
        <div class="skills-table">
          <div class="skills-header">
            <span>Навык</span>
            <span>Владею</span>
            <span>Не знаю</span>
          </div>
          <div v-for="(skill, index) in optionalSkills" :key="index" class="skills-row">
            <span class="skill-name">{{ skill }}</span>
            <div class="checkbox-cell">
              <input type="radio" :name="'optional-' + index" value="know" v-model="optionalStatus[index]" />
            </div>
            <div class="checkbox-cell">
              <input type="radio" :name="'optional-' + index" value="dontknow" v-model="optionalStatus[index]" />
            </div>
          </div>
        </div>
      </div>

      <button @click="handleContinue" :disabled="loading">
        {{ loading ? 'Загрузка...' : 'Продолжить' }}
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getAnalysisResult } from '../mocks/skills.js'
import { skillsApi } from '../api/skills'

const router = useRouter()

const jobTitle = 'Data Scientist' 
const analysisData = ref(getAnalysisResult(jobTitle))

const mandatorySkills = ref([])
const optionalSkills = ref([])

const mandatoryStatus = ref([])
const optionalStatus = ref([])
const loading = ref(false)

const errorMessage = ref('')

const resetSkills = () => {
  mandatoryStatus.value = mandatorySkills.value.map(() => null)
  optionalStatus.value = optionalSkills.value.map(() => null)
  localStorage.removeItem('user_skills_answers')
  successMessage.value = ''
}

const STORAGE_KEY = 'user_skills_answers'

const saveAnswers = () => {
  const data = {
    mandatoryStatus: mandatoryStatus.value,
    optionalStatus: optionalStatus.value,
    jobTitle: analysisData.value.jobTitle
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

const loadSavedAnswers = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    const data = JSON.parse(saved)
    if (data.mandatoryStatus) mandatoryStatus.value = data.mandatoryStatus
    if (data.optionalStatus) optionalStatus.value = data.optionalStatus
  }
}

watch([mandatoryStatus, optionalStatus], () => {
  saveAnswers()
}, { deep: true })

onMounted(() => {
  analysisData.value.skills.forEach(skill => {
    if (skill.importance === 'mandatory') {
      mandatorySkills.value.push(skill.name)
    } else if (skill.importance === 'optional') {
      optionalSkills.value.push(skill.name)
    }
  })
  
  mandatoryStatus.value = mandatorySkills.value.map(() => null)
  optionalStatus.value = optionalSkills.value.map(() => null)
  
  loadSavedAnswers()  
})

const handleContinue = () => {
  const mandatoryAnswers = mandatoryStatus.value.map((status, idx) => ({
    skill: mandatorySkills.value[idx],
    status: status === 'know' ? 'владею' : 'не знаю'
  }))
  
  const optionalAnswers = optionalStatus.value.map((status, idx) => ({
    skill: optionalSkills.value[idx],
    status: status === 'know' ? 'владею' : 'не знаю'
  }))

  const hasUnanswered = [...mandatoryStatus.value, ...optionalStatus.value].some(s => s === null)
  if (hasUnanswered) {
    errorMessage.value = 'Отметьте "Владею" или "Не знаю" для всех навыков'
    return
  }
  errorMessage.value = ''
  
  console.log('Должность:', analysisData.value.jobTitle)
  console.log('Всего вакансий:', analysisData.value.totalVacancies)
  console.log('Обязательные:', mandatoryAnswers)
  console.log('Необязательные:', optionalAnswers)
  
  router.push('/questions')
}
</script>

<style scoped>
.vacancy-page {
  min-height: 80vh;
  background-color: #f5f5f5;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.vacancy-card {
  max-width: 800px;
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.vacancy-title {
  font-size: 24px;
  font-weight: 600;
  color: #7a4e30;
  margin-bottom: 25px;
  text-align: center;
  -webkit-text-stroke: 0.5px #7a4e30;
}

.skills-section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid;
}

.section-title.mandatory {
  color: #7a4e30;
  border-bottom-color: #7a4e30;
}

.section-title.optional {
  color: #7a4e30;
  border-bottom-color: #7a4e30;
}

.skills-table {
  width: 100%;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
}

.skills-header {
  display: grid;
  grid-template-columns: 1fr 80px 80px;
  background-color: #c0950813;
  padding: 12px 16px;
  font-weight: 600;
  color: #7a4e30;
  border-bottom: 1px solid #eee;
}

.skills-row {
  display: grid;
  grid-template-columns: 1fr 80px 80px;
  padding: 10px 16px;
  border-bottom: 1px solid #f0f0f0;
  align-items: center;
}

.skills-row:last-child {
  border-bottom: none;
}

.skill-name {
  font-size: 15px;
  color: #333;
  text-align: left;
}

.checkbox-cell {
  text-align: center;
}

.checkbox-cell input[type="radio"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #3de0cd;
}

button {
  width: 100%;
  padding: 12px;
  margin-top: 20px;
  background-color: #3de0cd;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

button:hover {
  background-color: #2abbaa;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.reset-btn-small {
  background: none;
  color: #d4c53d;
  padding: 5px 12px;
  font-size: 13px;
  border-radius: 20px;
  cursor: pointer;
  margin: 0;
  width: auto;
  float: right;
  //border: 1px solid #e74c3c;
}

.reset-btn-small:hover {
  background-color: #d4ca3d;
  color: white;
}

.error {
  color: #e74c3c;
  margin-top: 10px;
  text-align: center;
}

@media (max-width: 600px) {
  .vacancy-card {
    padding: 20px;
  }
  
  .vacancy-title {
    font-size: 20px;
  }
  
  .section-title {
    font-size: 16px;
  }
  
  .skills-header,
  .skills-row {
    grid-template-columns: 1fr 50px 50px;
    padding: 8px 12px;
  }
  
  .skill-name {
    font-size: 13px;
  }
}
</style>