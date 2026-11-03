<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api'
import { CONDITION_TEXT, QUEST_TYPE_TEXT, yesNo } from '@/labels'
import DataTable from '@/components/DataTable.vue'

const error = ref('')
const empty = ref('')
const quests = ref([])

const rows = computed(() => quests.value.map((q) => ({
  任務編號: q['任務編號'],
  任務名稱: q['任務名稱'],
  任務類型: QUEST_TYPE_TEXT[q['任務類型']] || q['任務類型'],
  任務條件: CONDITION_TEXT[q['任務條件類型']] || q['任務條件類型'],
  條件數值: q['任務條件數值'],
  獎勵經驗: q['獎勵經驗'],
  獎勵金幣: q['獎勵金幣'],
  可重複: yesNo(q['是否為重複任務']),
  啟用狀態: q['任務是否啟用'] ? '啟用中' : '已停用'
})))

onMounted(async () => {
  const { ok, data } = await api('/api/quests')
  if (!ok) {
    error.value = data.message || '無法載入任務'
  } else if (!(data.data || []).length) {
    empty.value = data.message || '無任務資料'
  } else {
    quests.value = data.data
  }
})
</script>

<template>
  <div v-if="error" class="t-error">{{ error }}</div>
  <div v-else-if="empty" class="t-info">{{ empty }}</div>
  <DataTable v-else-if="rows.length" :rows="rows" />
</template>
