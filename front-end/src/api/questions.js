import api from './axios'

export const questionsApi = {
  saveUserPreferences(preferences) {
    return api.post('/user/preferences', preferences)
  }
}