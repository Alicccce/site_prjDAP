<template>
  <div class="vacancy-page">
    <div class="vacancy-card">
      <h1 class="vacancy-title">Должность: {{ vacancy.title }}</h1>

      <!-- Обязательные навыки -->
      <div class="skills-section">
        <h2 class="section-title mandatory">Обязательные навыки:</h2>
        <div class="skills-table">
          <div class="skills-header">
            <span>Навык</span>
            <span>Владею</span>
            <span>Не знаю</span>
          </div>
          <div v-for="(skill, index) in vacancy.mandatory" :key="index" class="skills-row">
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
      <div class="skills-section">
        <h2 class="section-title optional">Необязательные навыки, но полезные в собеседовании:</h2>
        <div class="skills-table">
          <div class="skills-header">
            <span>Навык</span>
            <span>Владею</span>
            <span>Не знаю</span>
          </div>
          <div v-for="(skill, index) in vacancy.optional" :key="index" class="skills-row">
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
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const vacancy = ref({
  title: 'Python-разработчик Junior',
  mandatory: [
    'Опыт программирования на Python от 1 года',
    'Умение работать с библиотеками для анализа данных',
    'Базовые знания принципов ООП и структур данных'
  ],
  optional: [
    'Опыт работы с API',
    'Знание основ Linux',
    'Понимание принципов ETL'
  ]
})

// Статусы: null - не выбрано, 'know' - владею, 'dontknow' - не знаю
const mandatoryStatus = ref(vacancy.value.mandatory.map(() => null))
const optionalStatus = ref(vacancy.value.optional.map(() => null))
const loading = ref(false)

const handleContinue = () => {
  // Собираем выбранные ответы
  const mandatoryAnswers = mandatoryStatus.value.map((status, idx) => ({
    skill: vacancy.value.mandatory[idx],
    status: status === 'know' ? 'владею' : 'не знаю'
  }))
  
  const optionalAnswers = optionalStatus.value.map((status, idx) => ({
    skill: vacancy.value.optional[idx],
    status: status === 'know' ? 'владею' : 'не знаю'
  }))
  
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
  margin-bottom: 30px;
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
  background-color: #f9f5f0;
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