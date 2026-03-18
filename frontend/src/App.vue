<template>
  <n-config-provider :theme="theme" :locale="zhCN">
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { zhCN, dateZhCN, darkTheme } from 'naive-ui'
import { useThemeStore } from '@/store/theme'

const themeStore = useThemeStore()
const theme = ref(themeStore.darkMode ? darkTheme : undefined)
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  min-height: 100vh;
}
</style>
