import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UserInfo } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserInfo | null>(null)

  const login = (userInfo: UserInfo, accessToken: string) => {
    user.value = userInfo
    token.value = accessToken
    localStorage.setItem('token', accessToken)
  }

  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  const isAuthenticated = () => !!token.value

  return {
    token,
    user,
    login,
    logout,
    isAuthenticated,
  }
})
