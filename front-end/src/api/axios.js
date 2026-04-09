import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api', // URL FastAPI
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Перехватчик для добавления токена
api.interceptors.request.use((config) => {
  const user = localStorage.getItem('user')
  if (user) {
    const userData = JSON.parse(user)
    if (userData.token) {
      config.headers.Authorization = `Bearer ${userData.token}`
    }
  }
  return config
})

export default api