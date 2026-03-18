import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'dashboard' },
      },
      {
        path: 'experiments',
        name: 'Experiments',
        component: () => import('@/views/Experiments.vue'),
        meta: { title: '实验管理', icon: 'flask' },
      },
      {
        path: 'experiments/:id',
        name: 'ExperimentDetail',
        component: () => import('@/views/ExperimentDetail.vue'),
        meta: { title: '实验详情', hidden: true },
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('@/views/Models.vue'),
        meta: { title: '模型管理', icon: 'robot' },
      },
      {
        path: 'training',
        name: 'Training',
        component: () => import('@/views/Training.vue'),
        meta: { title: '训练任务', icon: 'analytics' },
      },
      {
        path: 'data',
        name: 'Data',
        component: () => import('@/views/Data.vue'),
        meta: { title: '数据管理', icon: 'database' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
