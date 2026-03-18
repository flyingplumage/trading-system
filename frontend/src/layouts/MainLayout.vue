<template>
  <n-layout has-sider class="layout">
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      :native-scrollbar="false"
    >
      <div class="logo">
        <span v-if="!collapsed">🦞 量化训练</span>
        <span v-else>🦞</span>
      </div>

      <n-menu
        v-model:value="activeKey"
        :options="menuOptions"
        :collapsed="collapsed"
        :collapsed-width="64"
        @update:value="handleMenuClick"
      />
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="header">
        <div class="header-left">
          <n-button quaternary circle @click="toggleCollapsed">
            <template #icon>
              <n-icon :component="collapsed ? MenuOutline : MenuFoldOutline" />
            </template>
          </n-button>
        </div>

        <div class="header-right">
          <n-button quaternary circle @click="toggleTheme">
            <template #icon>
              <n-icon :component="darkMode ? SunnyOutline : MoonOutline" />
            </template>
          </n-button>

          <n-dropdown :options="userMenuOptions" @select="handleUserMenu">
            <n-button quaternary circle>
              <template #icon>
                <n-icon :component="PersonCircleOutline" />
              </template>
            </n-button>
          </n-dropdown>
        </div>
      </n-layout-header>

      <n-layout-content class="content">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useThemeStore } from '@/store/theme'
import type { MenuOption, DropdownOption } from 'naive-ui'
import {
  MenuOutline,
  MenuFoldOutline,
  SunnyOutline,
  MoonOutline,
  PersonCircleOutline,
  DashboardOutline,
  FlaskOutline,
  RobotOutline,
  AnalyticsOutline,
  DatabaseOutline,
  LogOutOutline,
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const collapsed = ref(false)
const activeKey = computed(() => route.name as string)
const darkMode = computed(() => themeStore.darkMode)

const renderIcon = (icon: any) => () => h(icon, { size: 20 })

const menuOptions: MenuOption[] = [
  {
    key: 'Dashboard',
    label: '仪表盘',
    icon: renderIcon(DashboardOutline),
  },
  {
    key: 'Experiments',
    label: '实验管理',
    icon: renderIcon(FlaskOutline),
  },
  {
    key: 'Models',
    label: '模型管理',
    icon: renderIcon(RobotOutline),
  },
  {
    key: 'Training',
    label: '训练任务',
    icon: renderIcon(AnalyticsOutline),
  },
  {
    key: 'Data',
    label: '数据管理',
    icon: renderIcon(DatabaseOutline),
  },
]

const userMenuOptions: DropdownOption[] = [
  {
    key: 'profile',
    label: '个人中心',
    icon: renderIcon(PersonCircleOutline),
  },
  {
    type: 'divider',
  },
  {
    key: 'logout',
    label: '退出登录',
    icon: renderIcon(LogOutOutline),
  },
]

const toggleCollapsed = () => {
  collapsed.value = !collapsed.value
}

const toggleTheme = () => {
  themeStore.toggleDark()
}

const handleMenuClick = (key: string) => {
  router.push(`/${key.toLowerCase()}`)
}

const handleUserMenu = (key: string) => {
  if (key === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  border-bottom: 1px solid #f0f0f0;
}

.header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.content {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 64px);
}
</style>
