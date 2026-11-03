<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const message = ref('')
const messageType = ref('')
const loading = ref(false)

function showMessage(text, type = '') {
  message.value = text
  messageType.value = type
}

async function login() {
  const name = username.value.trim()
  if (!name || !password.value) {
    showMessage('請輸入帳號與密碼', 'is-error')
    return
  }

  loading.value = true
  showMessage('登入中…')
  const { ok, data } = await api('/api/students/login', {
    method: 'POST',
    json: { username: name, password: password.value }
  })
  loading.value = false

  if (!ok) {
    showMessage(data.message || '登入失敗', 'is-error')
    return
  }
  const studentName = (data.user && data.user.student_name) || name
  showMessage('登入成功，' + studentName + ' 你好！正在進入主頁…', 'is-ok')
  router.push('/student/home')
}
</script>

<template>
  <main class="stage" aria-label="學生登入畫面">
    <img class="stage__bg" src="/assets/material/login.JPG" alt="Melody Town 學生登入背景" draggable="false">

    <form class="login-form" autocomplete="on" @submit.prevent="login">
      <label class="sr-only" for="username">帳號</label>
      <input
        id="username"
        v-model="username"
        class="field field--username"
        name="username"
        type="text"
        maxlength="50"
        required
      >

      <label class="sr-only" for="password">密碼</label>
      <input
        id="password"
        v-model="password"
        class="field field--password"
        name="password"
        type="password"
        maxlength="100"
        required
      >

      <button class="harp-btn" type="submit" title="登入" aria-label="登入" :disabled="loading"></button>
    </form>

    <p class="message" :class="messageType" role="status" aria-live="polite">{{ message }}</p>
  </main>
</template>

<style scoped src="@/styles/student/login.css"></style>
