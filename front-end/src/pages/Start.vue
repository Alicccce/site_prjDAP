<template>
  <div class="button-page">
    <div class="buttons-container">
      <button class="btn btn-left" @click="$router.push('/search')">
        <span class="btn-text">ЗНАЮ ЧЕГО ХОЧУ</span>
      </button>
      <button class="btn btn-right" @click="$router.push('/choice')">
        <span class="btn-text">НЕ ЗНАЮ ЧЕГО ХОЧУ</span>
      </button>
    </div>
    <p class="admin-message">{{ adminText }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const adminText = ref('Добро пожаловать! Мы поможем тебе составить план обучения навыков:)\nМного всего тебе расскажем и покажем. Твоя задача следовать инструкциям.')

</script>

<style scoped>
.button-page {
  min-height: 60vh;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 50px;
}

.buttons-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 500px;
  width: 100%;
  max-width: 1200px;
  padding: 0 200px;
}

.btn {
  flex: 1;
  max-width: 250px;
  padding: 16px 32px;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.4s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-left {
  background: linear-gradient(135deg, #7a4e30, #5a3b25);
  color: white;
}

.btn-left:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.btn-right {
  background: linear-gradient(135deg, #3de0cd, #2abbaa);
  color: white;
}

.btn-right:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.admin-message {
  text-align: center;
  font-size: 20px;
  color: #000000;
  padding: 12px 24px;
  max-width: 52%;
  line-height: 0,5;
  -webkit-text-stroke: 0,8px #7a4e30;
}
</style>