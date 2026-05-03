import api from './axios'

export const skillsApi = {
  saveUserSkills(skillsData) {
    return api.post('/user/skills', skillsData)
  },

  analyze(data) {
  return api.post('/ai/analyze-skills', data)
  }
}

