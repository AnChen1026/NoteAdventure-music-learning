<script setup>
import { onMounted, ref } from 'vue'
import { api } from '@/api'
import DataTable from '@/components/DataTable.vue'

const error = ref('')
const empty = ref('')
const rows = ref([])

onMounted(async () => {
  const { ok, data } = await api('/api/students')
  if (!ok) {
    error.value = data.message || '無法載入學生'
  } else if (!(data.data || []).length) {
    empty.value = data.message || '沒有學生資料'
  } else {
    rows.value = data.data
  }
})
</script>

<template>
  <div v-if="error" class="t-error">{{ error }}</div>
  <div v-else-if="empty" class="t-info">{{ empty }}</div>
  <DataTable v-else-if="rows.length" :rows="rows" />
</template>
