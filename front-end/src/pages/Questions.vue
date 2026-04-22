<template>
  <div class="quest-page">
    <div class="quest-card">
      <h1 class="title"> {{ quest.title }}</h1>
      <button @click="$router.push('/plan')" :disabled="loading">
        {{ loading ? 'Загрузка...' : 'Продолжить' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const quest = ref({
  title: 'Блок вопросов'
})

</script>

<style scoped>
.quest-page {
  min-height: 80vh;
  background-color: #f5f5f5;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.quest-card {
  max-width: 800px;
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 24px;
  font-weight: 600;
  color: #7a4e30;
  margin-bottom: 30px;
  text-align: center;
  -webkit-text-stroke: 0.5px #7a4e30;
}

button {
  width: 100%;
  padding: 12px;
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
</style>