import axios from 'axios'

// В dev-режиме Vite проксирует /api → http://localhost:8000/api
// В продакшне используем полный URL из переменной окружения
const baseURL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL,
})

// Перехватчик для добавления токена авторизации
api.interceptors.request.use((config) => {
  const user = localStorage.getItem('user')
  if (user) {
    try {
      const userData = JSON.parse(user)
      if (userData.token) {
        config.headers.Authorization = `Bearer ${userData.token}`
      }
    } catch (e) {
      // ignore malformed user data
    }
  }
  return config
})

export default api
