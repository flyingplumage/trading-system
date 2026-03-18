<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">🦞 量化训练系统</h1>
        <p class="login-subtitle">Quantitative Trading System</p>
      </div>

      <n-form
        ref="formRef"
        :model="form"
        :rules="rules"
        size="large"
        @keyup.enter="handleLogin"
      >
        <n-form-item path="username">
          <n-input
            v-model:value="form.username"
            placeholder="用户名"
            :input-props="{ autocomplete: 'username' }"
          >
            <template #prefix>
              <n-icon :component="PersonOutline" />
            </template>
          </n-input>
        </n-form-item>

        <n-form-item path="password">
          <n-input
            v-model:value="form.password"
            type="password"
            placeholder="密码"
            show-password-on="click"
            :input-props="{ autocomplete: 'current-password' }"
          >
            <template #prefix>
              <n-icon :component="LockClosedOutline" />
            </template>
          </n-input>
        </n-form-item>

        <n-button
          type="primary"
          size="large"
          block
          :loading="loading"
          @click="handleLogin"
        >
          登录
        </n-button>
      </n-form>

      <div class="login-tips">
        <n-text depth="3" style="font-size: 12px">
          默认账号：admin / admin123
        </n-text>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'naive-ui'
import { PersonOutline, LockClosedOutline } from '@vicons/ionicons5'
import { useAuthStore } from '@/store/auth'
import { authApi } from '@/services/api'
import type { FormInst, FormRules } from 'naive-ui'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: {
    required: true,
    message: '请输入用户名',
    trigger: 'blur',
  },
  password: {
    required: true,
    message: '请输入密码',
    trigger: 'blur',
  },
}

const handleLogin = async () => {
  await formRef.value?.validate()
  loading.value = true

  try {
    const res = await authApi.login(form)
    if (res.success) {
      authStore.login(res.data.user, res.data.access_token)
      message.success('登录成功')
      router.push('/dashboard')
    }
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.login-tips {
  text-align: center;
  margin-top: 16px;
}
</style>
