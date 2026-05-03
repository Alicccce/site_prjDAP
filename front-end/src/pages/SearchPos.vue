<template>
  <div class="search-page">
    <h3>Поиск требований</h3>
    <input type="text" placeholder="Введите название должности" v-model="query" @keyup.enter="handleSearch"/>
    <p v-if="error" class="error">{{ error }}</p>
    <button @click="handleSearch" :disabled="store.loading">
      {{ store.loading ? 'Загрузка...' : 'Анализировать' }}
    </button>
    <div v-if="store.loading" class="loader"></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchStore } from '../stores/search'

const router = useRouter()
const query = ref('')
const error = ref('')
const store = useSearchStore()

const handleSearch = async () => {
  error.value = ''
  const letterCount = (query.value.match(/[a-zA-Zа-яА-Я]/g) || []).length
  if (!query.value) {
    error.value = 'Введите запрос'
    return
  }
  if (query.value.length < 6) {
    error.value = 'Минимум 6 символов'
    return
  }
  if (letterCount < 3) {
    error.value = 'Минимум 3 буквы'
    return
  }

  try {
    await store.search(query.value)
    router.push('/skills')
  } catch (err) {
    error.value = store.error || 'Ошибка запроса. Попробуйте ещё раз.'
  }
}
</script>

<style scoped>
.search-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  min-height: 80vh;
  background-color: #f5f5f5;
  padding-top: 50px;
}

.search-page h3 {
  padding: 12px;
  margin-bottom: 5px;
  -webkit-text-stroke: 0.7px #7a4e30;
  color: #7a4e30;
}

input {
  width: 740px;
  padding: 12px;
  margin: 10px 0;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

button {
  order: 2;
  width: 740px;
  padding: 12px;
  margin-top: 5px;
  background-color: #7a4e30;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

button:hover {
  background-color: #5a3b25;
}

.loader {
  order: 3;
  margin: 20px auto;
  border: 4px solid #7a4e30;
  border-top: 4px solid #3de0cd;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.error {
  order: 1;
  color: red;
  font-size: 12px;
  width: 740px;
  text-align: left;
}
</style>