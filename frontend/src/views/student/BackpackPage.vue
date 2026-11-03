<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api'
import { session } from '@/session'

const SLOT_COUNT = 30
const items = ref([])
const message = ref('')

// 固定 30 格；只放虛擬商品
const slots = computed(() => Array.from({ length: SLOT_COUNT }, (_, i) => items.value[i] || null))

onMounted(async () => {
  const { ok, data } = await api(`/api/students/${session.user.student_id}/purchases`)
  if (!ok) {
    message.value = data.message || '無法載入背包'
    return
  }
  const all = Array.isArray(data.data) ? data.data : []
  items.value = all.filter((item) => item && item.item_type === 'VIRTUAL').slice(0, SLOT_COUNT)
})
</script>

<template>
  <main class="stage" aria-label="學生背包">
    <img class="stage__bg" src="/assets/material/backpack.JPG" alt="Melody Town 背包背景" draggable="false">

    <section class="backpack-grid" aria-label="持有的虛擬商品">
      <div
        v-for="(item, index) in slots"
        :key="index"
        class="backpack-slot"
        :class="{ 'is-filled': item }"
        role="listitem"
        :title="item ? item.item_name : undefined"
        :aria-label="item ? undefined : '空格子'"
      >
        <span v-if="item" class="backpack-slot__name">{{ item.item_name || '未命名商品' }}</span>
      </div>
    </section>

    <p class="backpack-message" :class="{ 'is-error': message }" role="status" aria-live="polite">{{ message }}</p>

    <router-link class="map-btn" to="/student/home" title="返回主頁" aria-label="MAP，返回主頁">
      <img class="map-btn__img" src="/assets/material/map_btn.png" alt="" draggable="false">
    </router-link>
  </main>
</template>

<style scoped src="@/styles/student/backpack.css"></style>
