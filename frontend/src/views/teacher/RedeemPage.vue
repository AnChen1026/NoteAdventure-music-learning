<script setup>
import { onMounted, ref } from 'vue'
import { api, formatDatetime } from '@/api'

const purchases = ref([])
const loaded = ref(false)
const empty = ref('')
const error = ref('')
const notice = ref('')
const busyId = ref(null)

async function load() {
  const { ok, data } = await api('/api/purchases/pending')
  loaded.value = true
  if (!ok) {
    error.value = data.message || '無法載入待兌換商品'
    return
  }
  purchases.value = data.data || []
  empty.value = purchases.value.length ? '' : data.message || '沒有待兌換的商品'
}

async function redeem(purchaseId) {
  busyId.value = purchaseId
  error.value = ''
  notice.value = ''
  const { ok, data } = await api(`/api/purchases/${purchaseId}/redeem`, { method: 'PATCH' })
  busyId.value = null
  if (!ok) {
    error.value = data.message || '兌換失敗'
    return
  }
  notice.value = data.message || '兌換完成'
  await load()
}

onMounted(load)
</script>

<template>
  <div v-if="notice" class="t-notice">{{ notice }}</div>
  <div v-if="error" class="t-error">{{ error }}</div>
  <div v-if="loaded && empty" class="t-info">{{ empty }}</div>
  <div v-for="p in purchases" :key="p.purchase_id" class="t-list-card">
    <strong>{{ p.student_name }}</strong>　{{ p.item_name }}
    <p class="t-caption">花費 {{ p.price }} 金幣　購買時間 {{ formatDatetime(p.created_at) }}</p>
    <button type="button" class="t-btn" :disabled="busyId === p.purchase_id" @click="redeem(p.purchase_id)">標記完成兌換</button>
  </div>
</template>
