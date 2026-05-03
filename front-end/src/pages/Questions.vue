<template>
  <div class="questions-page">
    <div class="questions-card">
      <h1 class="questions-title">Блок вопросов</h1>
      <button @click="resetAnswers" class="reset-btn-small">Сбросить ответы</button>

      <!-- Вопрос 1: Уровень -->
      <div class="question-block">
        <label class="question-label">1. Какого уровня вы хотите достичь?</label>
        <div class="button-group">
          <button 
            v-for="level in levels" 
            :key="level.value"
            :class="['level-btn', { active: answers.level === level.value }]"
            @click="answers.level = level.value"
          >
            {{ level.label }}
          </button>
        </div>
        <p v-if="errors.level" class="error">{{ errors.level }}</p>
      </div>

      <!-- Вопрос 2: Срок -->
      <div class="question-block">
        <label class="question-label">2. За какой срок?</label>
        <input 
          type="text" 
          v-model="answers.period" 
          placeholder="например: 3,5 месяца, 1 год, полгода"
          class="text-input"
        />
        <p v-if="errors.period" class="error">{{ errors.period }}</p>
      </div>

      <!-- Вопрос 3: Время в день -->
      <div class="question-block">
        <label class="question-label">3. Сколько времени в день вы готовы тратить на обучение?</label>
        <div class="time-options">
          <select v-model="answers.timePerDay" class="select-input">
            <option value="">Выберите вариант</option>
            <option value="30">до 30-40 минут</option>
            <option value="60">от часа до двух</option>
            <option value="120">3-4 часа</option>
            <option value="180">5 часов и больше</option>
          </select>
        </div>
        <p v-if="errors.timePerDay" class="error">{{ errors.timePerDay }}</p>
      </div>

      <!-- Вопрос 4: Готовность платить -->
      <div class="question-block">
        <label class="question-label">4. Вы готовы платить за доп. обучение?</label>
        <div class="button-group">
          <button 
            v-for="option in paymentOptions" 
            :key="option.value"
            :class="['payment-btn', { active: answers.paymentType === option.value }]"
            @click="answers.paymentType = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <p v-if="errors.paymentType" class="error">{{ errors.paymentType }}</p>
      </div>

      <!-- Кнопка отправки -->
      <button @click="submitAnswers" :disabled="loading" class="submit-btn">
        {{ loading ? 'Отправка...' : 'Составить план' }}
      </button>

      <!-- Сообщение об успехе/ошибке -->
      <p v-if="successMessage" class="success">{{ successMessage }}</p>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { questionsApi } from '../api/questions'

const router = useRouter()

const answers = ref({
  level: '',
  period: '',
  timePerDay: '',
  paymentType: ''
})

const errors = ref({
  level: '',
  period: '',
  timePerDay: '',
  paymentType: ''
})

const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const levels = [
  { value: 'minimal', label: 'Минимальный' },
  { value: 'middle', label: 'Средний' },
  { value: 'advanced', label: 'Продвинутый' },
  { value: 'very_high', label: 'Очень высокий' }
]

const paymentOptions = [
  { value: 'free', label: 'Только бесплатные' },
  { value: 'paid', label: 'Только платные' },
  { value: 'mixed', label: '50/50' }
]

const resetAnswers = () => {
  answers.value = { level: '', period: '', timePerDay: '', paymentType: '' }
  localStorage.removeItem(STORAGE_KEY)
  successMessage.value = ''
  errorMessage.value = ''
}

const STORAGE_KEY = 'user_questions_answers'

const saveToLocalStorage = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(answers.value))
}

const loadFromLocalStorage = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    answers.value = JSON.parse(saved)
  }
}

const validateForm = () => {
  let isValid = true
  errors.value = {
    level: '',
    period: '',
    timePerDay: '',
    paymentType: ''
  }

  if (!answers.value.level) {
    errors.value.level = 'Выберите уровень'
    isValid = false
  }

  if (!answers.value.period || answers.value.period.trim().length < 2) {
    errors.value.period = 'Введите срок обучения'
    isValid = false
  }

  if (!answers.value.timePerDay) {
    errors.value.timePerDay = 'Выберите время в день'
    isValid = false
  }

  if (!answers.value.paymentType) {
    errors.value.paymentType = 'Выберите вариант оплаты'
    isValid = false
  }

  return isValid
}

// отправка на бэк
const submitAnswers = async () => {
  if (!validateForm()) return

  loading.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    // Сохраняем ответы в localStorage для PlanP.vue
    localStorage.setItem(STORAGE_KEY, JSON.stringify(answers.value))

    successMessage.value = 'Составляем план...'
    setTimeout(() => {
      router.push('/plan')
    }, 800)

  } catch (error) {
    errorMessage.value = 'Ошибка. Попробуйте ещё раз.'
  } finally {
    loading.value = false
  }
}

watch(answers, () => {
  saveToLocalStorage()
}, { deep: true })

onMounted(() => {
  loadFromLocalStorage()
})
</script>

<style scoped>
.questions-page {
  min-height: 80vh;
  background-color: #f5f5f5;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.questions-card {
  max-width: 700px;
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.questions-title {
  font-size: 24px;
  font-weight: 600;
  color: #7a4e30;
  margin-bottom: 30px;
  text-align: center;
  -webkit-text-stroke: 0.5px #7a4e30;
}

.question-block {
  margin-bottom: 30px;
}

.question-label {
  display: block;
  font-size: 18px;
  color: #333;
  margin-bottom: 15px;
}

.button-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.level-btn, .payment-btn {
  padding: 10px 10px;
  border: 1.5px solid #7a4e30;
  background: white;
  color: #7a4e30;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  width: 24%;
}

.level-btn:hover, .payment-btn:hover {
  background-color: #c0950813;
}

.level-btn.active, .payment-btn.active {
  background-color: #7a4e30;
  color: white;
}

.text-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  box-sizing: border-box;
}

.text-input:focus {
  outline: none;
  border-color: #7a4e30;
}

.select-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  background: white;
  cursor: pointer;
}

.select-input:focus {
  outline: none;
  border-color: #7a4e30;
}

.time-options {
  width: 100%;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background-color: #3de0cd;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  font-weight: 500;
  margin-top: 20px;
  transition: background 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  background-color: #2abbaa;
}

.submit-btn:disabled {
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
  border: none;
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
  font-size: 13px;
  margin-top: 8px;
}

.success {
  color: #27ae60;
  font-size: 14px;
  margin-top: 15px;
  text-align: center;
}

@media (max-width: 600px) {
  .questions-card {
    padding: 20px;
  }
  
  .questions-title {
    font-size: 24px;
  }
  
  .question-label {
    font-size: 16px;
  }
  
  .button-group {
    gap: 10px;
  }
  
  .level-btn, .payment-btn {
    padding: 8px 16px;
    font-size: 12px;
  }
}
</style>