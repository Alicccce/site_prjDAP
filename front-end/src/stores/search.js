import { defineStore } from 'pinia'

export const useSearchStore = defineStore('search', {
  state: () => ({
    results: [],
    loading: false,
    error: null
  }),

  actions: {
    async search(query) {
      this.loading = true
      this.error = null

      try {
        // MOCK вместо hh.ru
        await new Promise(r => setTimeout(r, 1500))

        this.results = [
          'Python',
          'SQL',
          'Machine Learning'
        ]

      } catch (e) {
        this.error = 'Ошибка запроса'
      } finally {
        this.loading = false
      }
    }
  }
})