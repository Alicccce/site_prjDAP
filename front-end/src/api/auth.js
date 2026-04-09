import api from './axios'

export const authApi = {
  login(email, password) {
    return api.post('/auth/login', { email, password })
  },
  
  register(name, email, password) {
    return api.post('/auth/register', { name, email, password })
  },
  
  logout() {
    localStorage.removeItem('user')
  }
}