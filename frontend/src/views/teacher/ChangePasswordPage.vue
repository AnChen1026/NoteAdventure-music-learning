<script setup>
import { ref } from 'vue'
import { api } from '@/api'

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const notice = ref('')

async function submit() {
  error.value = ''
  notice.value = ''
  loading.value = true
  const { ok, data } = await api('/api/teachers/change-password', {
    method: 'POST',
    json: {
      old_password: oldPassword.value,
      new_password: newPassword.value,
      confirm_password: confirmPassword.value
    }
  })
  loading.value = false
  if (!ok) {
    error.value = data.message || '密碼修改失敗'
    return
  }
  notice.value = data.message || '密碼修改成功'
  oldPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
}
</script>

<template>
  <div class="t-card">
    <form class="t-form" @submit.prevent="submit">
      <label class="t-field">目前密碼<input v-model="oldPassword" type="password" autocomplete="current-password"></label>
      <label class="t-field">新密碼<input v-model="newPassword" type="password" autocomplete="new-password"></label>
      <label class="t-field">確認新密碼<input v-model="confirmPassword" type="password" autocomplete="new-password"></label>
      <button class="t-btn t-btn--primary" type="submit" :disabled="loading">確認修改</button>
    </form>
    <div v-if="error" class="t-error">{{ error }}</div>
    <div v-if="notice" class="t-notice">{{ notice }}</div>
  </div>
</template>
