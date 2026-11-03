<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api, formatDatetime } from '@/api'
import DataTable from '@/components/DataTable.vue'

const students = ref([])
const studentId = ref('')
const uploads = ref([])
const error = ref('')
const empty = ref('')

const rows = computed(() => uploads.value.map((u) => ({
  編號: u.upload_id,
  學生: u.student_name,
  曲目: u.song_name,
  秒數: u.audio_duration,
  上傳時間: formatDatetime(u.created_at)
})))

async function loadUploads() {
  error.value = ''
  empty.value = ''
  uploads.value = []
  const { ok, data } = await api('/api/practice-uploads', { params: { student_id: studentId.value } })
  if (!ok) {
    error.value = data.message || '無法載入上傳紀錄'
  } else if (!(data.data || []).length) {
    empty.value = data.message || '無上傳紀錄'
  } else {
    uploads.value = data.data
  }
}

onMounted(async () => {
  const { ok, data } = await api('/api/students')
  if (ok) {
    students.value = data.data || []
  }
  await loadUploads()
})

watch(studentId, loadUploads)
</script>

<template>
  <label v-if="students.length" class="t-field" style="max-width: 320px; margin-bottom: 1rem">查看哪一位學生
    <select v-model="studentId">
      <option value="">全部學生</option>
      <option v-for="s in students" :key="s['序號']" :value="s['序號']">{{ s['姓名'] }}</option>
    </select>
  </label>

  <div v-if="error" class="t-error">{{ error }}</div>
  <div v-else-if="empty" class="t-info">{{ empty }}</div>
  <template v-else-if="uploads.length">
    <DataTable :rows="rows" />

    <h2>試聽錄音</h2>
    <p class="t-caption">點播放即可聽學生上傳的練習音檔（最多顯示最近 20 筆）。</p>
    <div v-for="u in uploads.slice(0, 20)" :key="u.upload_id" class="t-list-card">
      <strong>{{ u.student_name }}｜{{ u.song_name }}｜{{ u.audio_duration }} 秒｜{{ formatDatetime(u.created_at) }}</strong>
      <audio controls preload="none" :src="`/api/practice-uploads/${u.upload_id}/audio`"></audio>
    </div>
  </template>
</template>
