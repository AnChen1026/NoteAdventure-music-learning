<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, formatDatetime } from '@/api'
import DataTable from '@/components/DataTable.vue'

const error = ref('')
const dashboard = ref(null)

const metrics = computed(() => {
  const s = (dashboard.value && dashboard.value.summary) || {}
  return [
    { label: '學生人數', value: s.student_count || 0 },
    { label: '啟用中任務', value: s.active_quest_count || 0 },
    { label: '進行中任務', value: s.active_assignment_count || 0 },
    { label: '已過期任務', value: s.expired_assignment_count || 0 },
    { label: '近 7 天上傳', value: s.upload_count_7d || 0 },
    { label: '待兌換商品', value: s.pending_redeem_count || 0 }
  ]
})

function list(key) {
  return ((dashboard.value && dashboard.value[key]) || []).slice(0, 5)
}

const students = computed(() => (dashboard.value && dashboard.value.students) || [])
const assignments = computed(() => list('active_assignments').map((item) => ({
  學生: item['學生'],
  任務: item['任務'],
  進度: `${item['目前進度'] || 0} / ${item['目標'] || 0}`,
  截止時間: formatDatetime(item['截止時間'])
})))
const uploads = computed(() => list('recent_uploads').map((item) => ({
  學生: item['學生'],
  曲目: item['曲目'],
  秒數: item['秒數'],
  上傳時間: formatDatetime(item['上傳時間'])
})))
const redeems = computed(() => list('pending_redeems').map((item) => ({
  學生: item['學生'],
  商品: item['商品'],
  價格: item['價格'],
  購買時間: formatDatetime(item['購買時間'])
})))

onMounted(async () => {
  const { ok, data } = await api('/api/dashboard')
  if (!ok) {
    error.value = data.message || '無法載入首頁資料'
    return
  }
  dashboard.value = data.data || {}
})
</script>

<template>
  <div v-if="error" class="t-error">{{ error }}</div>
  <template v-else-if="dashboard">
    <div class="t-metrics">
      <div v-for="metric in metrics" :key="metric.label" class="t-metric">
        <div class="t-metric__label">{{ metric.label }}</div>
        <div class="t-metric__value">{{ metric.value }}</div>
      </div>
    </div>

    <h2>學生概況</h2>
    <DataTable v-if="students.length" :rows="students" />
    <div v-else class="t-info">尚無學生</div>

    <h2>進行中任務（最近 5 筆）</h2>
    <DataTable v-if="assignments.length" :rows="assignments" />
    <div v-else class="t-info">目前沒有進行中的任務</div>

    <h2>最近上傳（最近 5 筆）</h2>
    <DataTable v-if="uploads.length" :rows="uploads" />
    <div v-else class="t-info">尚無上傳紀錄</div>

    <h2>待兌換商品（最近 5 筆）</h2>
    <DataTable v-if="redeems.length" :rows="redeems" />
    <div v-else class="t-info">目前沒有待兌換商品</div>
  </template>
</template>
