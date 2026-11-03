<script setup>
import { ref } from 'vue'
import { api } from '@/api'

const studentName = ref('')
const loading = ref(false)
const error = ref('')
const warning = ref('')
const result = ref(null)

async function submit() {
  error.value = ''
  warning.value = ''
  result.value = null
  if (studentName.value.trim() === '') {
    warning.value = '學生姓名不可空白'
    return
  }
  loading.value = true
  const { ok, data } = await api('/api/students', { method: 'POST', json: { student_name: studentName.value.trim() } })
  loading.value = false
  if (!ok) {
    error.value = data.message || '建立失敗'
    return
  }
  result.value = data
  studentName.value = ''
}
</script>

<template>
  <div class="t-card">
    <p class="t-caption">建立後系統會自動產生學生帳號與臨時密碼。</p>
    <form class="t-form" @submit.prevent="submit">
      <label class="t-field">學生姓名<input v-model="studentName" type="text" maxlength="50"></label>
      <button class="t-btn t-btn--primary" type="submit" :disabled="loading">建立</button>
    </form>
    <div v-if="warning" class="t-warning">{{ warning }}</div>
    <div v-if="error" class="t-error">{{ error }}</div>
    <template v-if="result">
      <div class="t-notice">{{ result.message || '建立成功' }}</div>
      <div class="t-code">帳號：{{ result.username }}
臨時密碼：{{ result.temp_password }}</div>
      <p class="t-caption">學生首次登入後必須修改密碼</p>
    </template>
  </div>
</template>
