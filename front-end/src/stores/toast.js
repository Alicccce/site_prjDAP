import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])
  let nextId = 0

  const add = (message, type = 'info', duration = 3500) => {
    const id = ++nextId
    toasts.value.push({ id, message, type })
    setTimeout(() => remove(id), duration)
  }

  const remove = (id) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const success = (msg, duration) => add(msg, 'success', duration)
  const error   = (msg, duration) => add(msg, 'error', duration)
  const info    = (msg, duration) => add(msg, 'info', duration)
  const warning = (msg, duration) => add(msg, 'warning', duration)

  return { toasts, add, remove, success, error, info, warning }
})
