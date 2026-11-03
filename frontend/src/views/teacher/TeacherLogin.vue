<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import '@/styles/teacher.css'

const router = useRouter()
const tab = ref('login')
const error = ref('')
const notice = ref('')
const loading = ref(false)

const email = ref('')
const password = ref('')

const teacherName = ref('')
const registerEmail = ref('')
const registerPassword = ref('')
const confirmPassword = ref('')

function switchTab(name) {
  tab.value = name
  error.value = ''
  notice.value = ''
}

async function login() {
  error.value = ''
  loading.value = true
  const { ok, data } = await api('/api/teachers/login', {
    method: 'POST',
    json: { email: email.value.trim(), password: password.value }
  })
  loading.value = false
  if (!ok) {
    error.value = data.message || '登入失敗'
    return
  }
  router.push('/teacher/dashboard')
}

async function register() {
  error.value = ''
  notice.value = ''
  if (!teacherName.value.trim() || !registerEmail.value.trim() || !registerPassword.value || !confirmPassword.value) {
    error.value = '請完整填寫姓名、電子信箱與密碼'
    return
  }
  if (registerPassword.value !== confirmPassword.value) {
    error.value = '兩次密碼不一致'
    return
  }
  loading.value = true
  const { ok, data } = await api('/api/teachers/register', {
    method: 'POST',
    json: {
      teacher_name: teacherName.value.trim(),
      email: registerEmail.value.trim(),
      password: registerPassword.value,
      confirm_password: confirmPassword.value
    }
  })
  loading.value = false
  if (!ok) {
    error.value = data.message || '註冊失敗'
    return
  }
  notice.value = data.message || '老師帳號建立成功'
  registerPassword.value = ''
  confirmPassword.value = ''
}

onMounted(() => document.documentElement.classList.add('na-teacher'))
onBeforeUnmount(() => document.documentElement.classList.remove('na-teacher'))
</script>

<template>
  <div class="t-login">
    <div class="t-card">
      <h1 class="t-login__title">NoteAdventure</h1>
      <p class="t-caption">老師管理後台</p>

      <div class="t-tabs" role="tablist">
        <button type="button" class="t-tab" :class="{ 'is-active': tab === 'login' }" @click="switchTab('login')">老師登入</button>
        <button type="button" class="t-tab" :class="{ 'is-active': tab === 'register' }" @click="switchTab('register')">老師註冊</button>
      </div>

      <form v-if="tab === 'login'" class="t-form" @submit.prevent="login">
        <label class="t-field">電子信箱<input v-model="email" type="email" autocomplete="username"></label>
        <label class="t-field">密碼<input v-model="password" type="password" autocomplete="current-password"></label>
        <button class="t-btn t-btn--primary" type="submit" :disabled="loading">登入</button>
      </form>

      <form v-else class="t-form" @submit.prevent="register">
        <p class="t-caption">註冊成功後，請回到「老師登入」使用電子信箱登入。</p>
        <label class="t-field">老師姓名<input v-model="teacherName" type="text"></label>
        <label class="t-field">電子信箱<input v-model="registerEmail" type="email"></label>
        <label class="t-field">密碼<input v-model="registerPassword" type="password" autocomplete="new-password"></label>
        <label class="t-field">確認密碼<input v-model="confirmPassword" type="password" autocomplete="new-password"></label>
        <button class="t-btn t-btn--primary" type="submit" :disabled="loading">註冊</button>
      </form>

      <div v-if="notice" class="t-notice">{{ notice }}</div>
      <div v-if="error" class="t-error">{{ error }}</div>
      <p class="t-caption" style="margin-top: 1.25rem">學生請開啟 <router-link to="/student/login">學生登入頁</router-link>。</p>
    </div>
  </div>
</template>
