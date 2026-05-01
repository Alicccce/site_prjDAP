import axios from 'axios'

const api = axios.create({
  baseURL: 'https://site-prjdapdep.onrender.com/api', 
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