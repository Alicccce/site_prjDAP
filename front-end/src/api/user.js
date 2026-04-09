import api from './axios'

export const userApi = {
  getProfile() {
    return api.get('/user/profile')
  },
  
  updateSkills(skills) {
    return api.put('/user/skills', { skills })
  },
  
  getLearningPlan() {
    return api.get('/user/plan')
  }
}