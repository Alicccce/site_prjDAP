import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/axios'

export const useBranch2Store = defineStore('branch2', () => {
  const filters = ref({
    specialization: '', industry: '', education: '',
    salaryFrom: '', salaryTo: '', schedule: []
  })
  const userSkills = ref([])
  const suggestedPositions = ref([])
  const selectedPosition = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const setFilters = (f) => { filters.value = { ...f } }

  const setSkills = (skills) => { userSkills.value = [...skills] }

  const fetchSuggestedPositions = async () => {
    loading.value = true
    error.value = null
    suggestedPositions.value = []
    try {
      const response = await api.post('/analyze/suggest-positions', {
        filters: {
          specialization: filters.value.specialization || '',
          industry: filters.value.industry || '',
          education: filters.value.education || '',
          salaryFrom: filters.value.salaryFrom ? Number(filters.value.salaryFrom) : null,
          salaryTo: filters.value.salaryTo ? Number(filters.value.salaryTo) : null,
          schedule: filters.value.schedule || []
        },
        user_skills: userSkills.value
      })
      suggestedPositions.value = response.data.positions || []
    } catch (e) {
      error.value = e.response?.data?.detail || 'Ошибка запроса к серверу'
      throw e
    } finally {
      loading.value = false
    }
  }

  const selectPosition = (position) => {
    selectedPosition.value = position
    if (position) {
      const skillsData = {
        jobTitle: position.title,
        totalVacancies: position.total_vacancies || 0,
        mandatory: (position.all_skills || [])
          .filter(s => s.importance === 'important')
          .map(s => ({
            skill: s.name, frequency: s.frequency,
            status: userSkills.value.some(u => u.toLowerCase() === s.name.toLowerCase()) ? 'владею' : 'не знаю'
          })),
        optional: (position.all_skills || [])
          .filter(s => s.importance !== 'important')
          .map(s => ({
            skill: s.name, frequency: s.frequency,
            status: userSkills.value.some(u => u.toLowerCase() === s.name.toLowerCase()) ? 'владею' : 'не знаю'
          }))
      }
      localStorage.setItem('skills_answers', JSON.stringify(skillsData))
    }
  }

  const reset = () => {
    filters.value = { specialization: '', industry: '', education: '', salaryFrom: '', salaryTo: '', schedule: [] }
    userSkills.value = []
    suggestedPositions.value = []
    selectedPosition.value = null
    error.value = null
  }

  return { filters, userSkills, suggestedPositions, selectedPosition, loading, error,
           setFilters, setSkills, fetchSuggestedPositions, selectPosition, reset }
})
