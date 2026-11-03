<script setup>
import { ref } from 'vue'
import { api } from '@/api'

const username = ref('')
const loading = ref(false)
const error = ref('')
const warning = ref('')
const result = ref(null)

async function submit() {
  error.value = ''
  warning.value = ''
  result.value = null
  if (username.value.trim() === '') {
    warning.value = '請輸入學生帳號'
    return
  }
  loading.value = true
  const { ok, data } = await api('/api/students/reset-password', { method: 'POST', json: { username: username.value.trim() } })
  loading.value = false
  if (!ok) {
    error.value = data.message || '重設失敗'
    return
  }
  result.value = data
}
</script>

<template>
  <div class="t-card">
    <p class="t-caption">重設後學生下次登入需重新修改密碼。</p>
    <form class="t-form" @submit.prevent="submit">
      <label class="t-field">學生帳號<input v-model="username" type="text" maxlength="50"></label>
      <button class="t-btn t-btn--primary" type="submit" :disabled="loading">重設密碼</button>
    </form>
    <div v-if="warning" class="t-warning">{{ warning }}</div>
    <div v-if="error" class="t-error">{{ error }}</div>
    <template v-if="result">
      <div class="t-notice">{{ result.message || '密碼重設成功' }}</div>
      <div class="t-code">臨時密碼：{{ result.temp_password }}</div>
    </template>
  </div>
</template>
