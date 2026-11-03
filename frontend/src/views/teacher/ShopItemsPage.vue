<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api'
import { ITEM_TYPE_TEXT } from '@/labels'
import DataTable from '@/components/DataTable.vue'

const error = ref('')
const empty = ref('')
const items = ref([])

const rows = computed(() => items.value.map((item) => ({
  商品編號: item.item_id,
  商品名稱: item.item_name,
  商品類型: ITEM_TYPE_TEXT[item.item_type] || item.item_type,
  價格: item.price,
  庫存: item.stock === null ? '不限量' : item.stock,
  說明: item.description || '無',
  狀態: item.is_active ? '上架中' : '已下架'
})))

onMounted(async () => {
  const { ok, data } = await api('/api/shop-items')
  if (!ok) {
    error.value = data.message || '無法載入商品'
  } else if (!(data.data || []).length) {
    empty.value = data.message || '無商品資料'
  } else {
    items.value = data.data
  }
})
</script>

<template>
  <div v-if="error" class="t-error">{{ error }}</div>
  <div v-else-if="empty" class="t-info">{{ empty }}</div>
  <DataTable v-else-if="rows.length" :rows="rows" />
</template>
