import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const darkMode = ref(false)

  const toggleDark = () => {
    darkMode.value = !darkMode.value
  }

  return {
    darkMode,
    toggleDark,
  }
})
