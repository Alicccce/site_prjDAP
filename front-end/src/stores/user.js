import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)

  const setUser = (userData) => {
    user.value = userData
    if (userData.token) {
      token.value = userData.token
      localStorage.setItem('token', userData.token)
    }
  }

  const clearUser = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  const isAuthenticated = () => !!token.value

  return { user, token, setUser, clearUser, isAuthenticated }
})