import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)

  const setUser = (userData) => {
  user.value = userData
  if (userData.access_token) {    
    token.value = userData.access_token
    localStorage.setItem('token', userData.access_token)
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