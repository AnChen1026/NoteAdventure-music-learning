<script setup>
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { clearSession } from '@/session'

const router = useRouter()

async function logout() {
  // 即使 API 失敗也導回登入頁
  await api('/api/logout', { method: 'POST' })
  clearSession()
  router.push('/student/login')
}
</script>

<template>
  <main class="stage" aria-label="學生主頁地圖">
    <img class="stage__bg" src="/assets/material/home.png" alt="Melody Town 學生主頁" draggable="false">

    <router-link class="hotspot hotspot--practice" to="/student/practice" title="琴房｜上傳練習" aria-label="琴房，前往上傳練習" />
    <router-link class="hotspot hotspot--pet" to="/student/pet" title="寵物" aria-label="寵物" />
    <router-link class="hotspot hotspot--shop" to="/student/shop" title="商店" aria-label="商店" />
    <router-link class="hotspot hotspot--quests" to="/student/quests" title="任務欄" aria-label="任務清單" />
    <router-link class="hotspot hotspot--class" to="/student/class" title="教室" aria-label="教室" />
    <router-link class="hotspot hotspot--backpack" to="/student/backpack" title="背包" aria-label="背包" />
    <router-link class="hotspot hotspot--settings" to="/student/settings" title="設定｜修改密碼" aria-label="設定，修改密碼" />

    <!-- 左下指北針：登出 -->
    <button type="button" class="hotspot hotspot--logout" title="登出" aria-label="登出" @click="logout"></button>
  </main>
</template>

<style scoped src="@/styles/student/home.css"></style>
