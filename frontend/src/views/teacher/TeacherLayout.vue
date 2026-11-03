<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { clearSession, session } from '@/session'
import '@/styles/teacher.css'

const route = useRoute()
const router = useRouter()

const NAV = [
  { group: '總覽', links: [{ to: '/teacher/dashboard', label: '首頁' }] },
  {
    group: '學生',
    links: [
      { to: '/teacher/students', label: '學生列表' },
      { to: '/teacher/students/new', label: '建立學生' },
      { to: '/teacher/students/reset-password', label: '重設學生密碼' }
    ]
  },
  {
    group: '任務',
    links: [
      { to: '/teacher/quests', label: '任務清單' },
      { to: '/teacher/quests/new', label: '新增任務' },
      { to: '/teacher/quests/assign', label: '指派任務' },
      { to: '/teacher/uploads', label: '上傳紀錄' }
    ]
  },
  {
    group: '商店',
    links: [
      { to: '/teacher/shop', label: '商品清單' },
      { to: '/teacher/shop/new', label: '新增商品' },
      { to: '/teacher/redeem', label: '待兌換商品' }
    ]
  },
  { group: '帳號', links: [{ to: '/teacher/password', label: '修改密碼' }] }
]

async function logout() {
  await api('/api/logout', { method: 'POST' })
  clearSession()
  router.push('/teacher/login')
}

onMounted(() => document.documentElement.classList.add('na-teacher'))
onBeforeUnmount(() => document.documentElement.classList.remove('na-teacher'))
</script>

<template>
  <div class="t-app">
    <aside class="t-sidebar">
      <p class="t-sidebar__name">{{ session.user ? session.user.teacher_name : '' }} 老師</p>
      <nav>
        <template v-for="section in NAV" :key="section.group">
          <p class="t-nav__group">{{ section.group }}</p>
          <router-link v-for="link in section.links" :key="link.to" class="t-nav__link" :to="link.to">
            {{ link.label }}
          </router-link>
        </template>
      </nav>
      <div class="t-sidebar__footer">
        <button type="button" class="t-btn" @click="logout">登出</button>
      </div>
    </aside>

    <main class="t-main">
      <h1>{{ route.meta.title }}</h1>
      <router-view :key="route.fullPath" />
    </main>
  </div>
</template>
