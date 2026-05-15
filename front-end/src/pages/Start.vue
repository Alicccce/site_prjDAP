<template>
  <div class="start_page">
    <p class="welcome-title">{{ adminText2 }}</p>

    <!-- Шаги онбординга -->
    <div class="steps-row">
      <div class="step">
        <div class="step-num">1</div>
        <div class="step-text">Введи желаемую должность или укажи свои навыки</div>
      </div>
      <div class="step-arrow">→</div>
      <div class="step">
        <div class="step-num">2</div>
        <div class="step-text">Отметь навыки которые уже знаешь</div>
      </div>
      <div class="step-arrow">→</div>
      <div class="step">
        <div class="step-num">3</div>
        <div class="step-text">Получи персональный план обучения с курсами</div>
      </div>
    </div>

    <div class="starts-container">
      <button class="btn btn-left" @click="$router.push('/search')">
        <span class="btn-icon">🎯</span>
        <span class="btn-text">ЗНАЮ ЧЕГО ХОЧУ</span>
        <span class="btn-hint">Знаю должность</span>
      </button>
      <button class="btn btn-right" @click="$router.push('/choice')">
        <span class="btn-icon">🔍</span>
        <span class="btn-text">НЕ ЗНАЮ ЧЕГО ХОЧУ</span>
        <span class="btn-hint">Помогите выбрать</span>
      </button>
    </div>

    <p class="admin-message">{{ adminText }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const adminText = ref([
  '💡Нажмите кнопку слева, если знаете должность, на которой хотели бы работать, вам нужно будет ввести конкретное название вакансии.', '',
  '🔦Нажмите кнопку справа, если слабо представляете, кем хотели бы работать, но у вас есть конкретные запросы и проф. навыки.',
].join('\n'))

const adminText2 = ref([
  'Добро пожаловать!',
  'Мы поможем вам составить план обучения навыкам:)', 
  'Но для начала нужно определиться с вашими запросами.', 
].join('\n'))

</script>

<style scoped>
.start_page {
  min-height: 70vh;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  gap: 32px;
}

.welcome-title {
  font-size: 22px;
  font-weight: 700;
  color: #7a4e30;
  text-align: center;
  white-space: pre-line;
  max-width: 600px;
  line-height: 1.5;
}

/* Шаги */
.steps-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 800px;
}
.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  max-width: 160px;
  text-align: center;
}
.step-num {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #7a4e30, #c09508);
  color: white;
  font-size: 16px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.step-text { font-size: 13px; color: #555; line-height: 1.4; }
.step-arrow { font-size: 20px; color: #c09508; font-weight: 700; }

/* Кнопки */
.starts-container {
  display: flex;
  justify-content: center;
  align-items: stretch;
  gap: 24px;
  flex-wrap: wrap;
}

.btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 220px;
  padding: 24px 20px;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}
.btn-icon { font-size: 28px; }
.btn-text { font-size: 15px; font-weight: 700; }
.btn-hint { font-size: 12px; opacity: 0.8; }

.btn-left {
  background: linear-gradient(135deg, #7a4e30, #5a3b25);
  color: white;
}
.btn-left:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(122,78,48,0.3); }

.btn-right {
  background: linear-gradient(135deg, #3de0cd, #2abbaa);
  color: white;
}
.btn-right:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(61,224,205,0.3); }

.admin-message {
  text-align: center;
  font-size: 14px;
  color: #888;
  max-width: 600px;
  white-space: pre-line;
  line-height: 1.6;
}

@media (max-width: 600px) {
  .step-arrow { display: none; }
  .steps-row { gap: 16px; }
  .btn { width: 100%; max-width: 300px; }
  .welcome-title { font-size: 18px; }
}
</style>