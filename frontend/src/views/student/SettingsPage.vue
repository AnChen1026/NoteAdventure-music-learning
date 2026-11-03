<script setup>
import { ref } from 'vue'
import { api } from '@/api'

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const message = ref('')
const messageType = ref('')

function showMessage(text, type = '') {
  message.value = text
  messageType.value = type
}

async function submit() {
  if (!oldPassword.value || !newPassword.value || !confirmPassword.value) {
    showMessage('請完整輸入舊密碼與新密碼', 'is-error')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    showMessage('兩次新密碼不一致', 'is-error')
    return
  }

  loading.value = true
  showMessage('修改中…')
  const { ok, data } = await api('/api/students/change-password', {
    method: 'POST',
    json: {
      old_password: oldPassword.value,
      new_password: newPassword.value,
      confirm_password: confirmPassword.value
    }
  })
  loading.value = false

  if (!ok) {
    showMessage(data.message || '密碼修改失敗', 'is-error')
    return
  }
  showMessage(data.message || '密碼修改成功', 'is-ok')
  oldPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
}
</script>

<template>
  <main class="stage" aria-label="學生修改密碼">
    <img class="stage__bg" src="/assets/material/settings.JPG" alt="Melody Town 設定頁背景" draggable="false">

    <section class="settings-panel" aria-label="修改密碼">
      <h1 class="settings-panel__title">修改密碼</h1>

      <form class="password-form" autocomplete="off" @submit.prevent="submit">
        <label class="field-row">
          <span class="field-row__label">目前密碼</span>
          <input v-model="oldPassword" class="field-row__input" type="password" maxlength="100" required>
        </label>
        <label class="field-row">
          <span class="field-row__label">新密碼</span>
          <input v-model="newPassword" class="field-row__input" type="password" maxlength="100" required>
        </label>
        <label class="field-row">
          <span class="field-row__label">確認新密碼</span>
          <input v-model="confirmPassword" class="field-row__input" type="password" maxlength="100" required>
        </label>
        <button class="submit-btn" type="submit" :disabled="loading">確認修改</button>
      </form>

      <p class="settings-message" :class="messageType" role="status" aria-live="polite">{{ message }}</p>
    </section>

    <router-link class="map-btn" to="/student/home" title="返回主頁" aria-label="MAP，返回主頁" />
  </main>
</template>

<style scoped src="@/styles/student/settings.css"></style>
