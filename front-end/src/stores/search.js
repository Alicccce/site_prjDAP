import { defineStore } from 'pinia'
import api from '../api/axios'

export const useSearchStore = defineStore('search', {
  state: () => ({
    results: null,   // { jobTitle, totalVacancies, skills: [{name, frequency, importance}] }
    loading: false,
    error: null
  }),

  actions: {
    async search(query) {
      this.loading = true
      this.error = null
      this.results = null

      try {
        const response = await api.post('/analyze/by-position', { query })
        const skills = response.data.skills || []
        const totalVacancies = response.data.total_vacancies || 0

        // Нормализуем importance: бэкенд возвращает "important"/"not_important"
        // Skills.vue ожидает "mandatory"/"optional"
        const normalizedSkills = skills.map(s => ({
          name: s.skill_name || s.name,
          frequency: s.frequency,
          importance: s.importance === 'important' ? 'mandatory' : 'optional'
        }))

        this.results = {
          jobTitle: query,
          totalVacancies,
          skills: normalizedSkills
        }

      } catch (e) {
        this.error = e.response?.data?.detail || 'Ошибка запроса к серверу'
        throw e
      } finally {
        this.loading = false
      }
    }
  }
})
