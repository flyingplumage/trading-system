import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SystemStats, TrainingTask } from '@/types'

export const useSystemStore = defineStore('system', () => {
  const stats = ref<SystemStats | null>(null)
  const tasks = ref<TrainingTask[]>([])
  const loading = ref(false)

  const setStats = (data: SystemStats) => {
    stats.value = data
  }

  const setTasks = (data: TrainingTask[]) => {
    tasks.value = data
  }

  const setLoading = (value: boolean) => {
    loading.value = value
  }

  return {
    stats,
    tasks,
    loading,
    setStats,
    setTasks,
    setLoading,
  }
})
