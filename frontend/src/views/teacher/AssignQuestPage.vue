<script setup>
import { onMounted, ref } from 'vue'
import { api, formatDatetime } from '@/api'

const quests = ref([])
const students = ref([])
const questId = ref(null)
const studentId = ref(null)
const loaded = ref(false)
const loading = ref(false)
const error = ref('')
const result = ref(null)

onMounted(async () => {
  const [questRes, studentRes] = await Promise.all([api('/api/quests'), api('/api/students')])
  if (!questRes.ok) {
    error.value = questRes.data.message || '無法載入任務'
    return
  }
  if (!studentRes.ok) {
    error.value = studentRes.data.message || '無法載入學生'
    return
  }
  // 只列出啟用中的任務
  quests.value = (questRes.data.data || []).filter((q) => q['任務是否啟用'])
  students.value = studentRes.data.data || []
  questId.value = quests.value.length ? quests.value[0]['任務編號'] : null
  studentId.value = students.value.length ? students.value[0]['序號'] : null
  loaded.value = true
})

async function submit() {
  error.value = ''
  result.value = null
  loading.value = true
  const { ok, data } = await api(`/api/quests/${questId.value}/assign`, {
    method: 'POST',
    json: { student_id: Number(studentId.value) }
  })
  loading.value = false
  if (!ok) {
    error.value = data.message || '任務指派失敗'
    return
  }
  result.value = data
}
</script>

<template>
  <div class="t-card">
    <template v-if="loaded">
      <div v-if="!quests.length" class="t-info">沒有可指派的啟用任務</div>
      <div v-else-if="!students.length" class="t-info">沒有學生資料</div>
      <form v-else class="t-form" @submit.prevent="submit">
        <label class="t-field">選擇任務
          <select v-model="questId">
            <option v-for="q in quests" :key="q['任務編號']" :value="q['任務編號']">{{ q['任務名稱'] }}</option>
          </select>
        </label>
        <label class="t-field">選擇學生
          <select v-model="studentId">
            <option v-for="s in students" :key="s['序號']" :value="s['序號']">{{ s['姓名'] }}（{{ s['帳號'] }}）</option>
          </select>
        </label>
        <button class="t-btn t-btn--primary" type="submit" :disabled="loading">確認指派</button>
      </form>
    </template>
    <div v-if="error" class="t-error">{{ error }}</div>
    <template v-if="result">
      <div class="t-notice">{{ result.message || '任務指派成功' }}</div>
      <p>期間：{{ result.period_key }}</p>
      <p>到期：{{ formatDatetime(result.expires_at) }}</p>
    </template>
  </div>
</template>
