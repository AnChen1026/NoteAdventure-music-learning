<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api'
import { session } from '@/session'

const stageOrder = ref(1)

// 階段 1 用 stage1 背景；2～4 用 stage2-4 背景
const stage = computed(() => Math.min(Math.max(Number(stageOrder.value) || 1, 1), 4))

onMounted(async () => {
  const { ok, data } = await api(`/api/students/${session.user.student_id}/pet`)
  if (ok) {
    stageOrder.value = (data.data || {}).stage_order
  }
})
</script>

<template>
  <main class="stage" aria-label="學生寵物房">
    <img
      class="stage__bg"
      :src="stage === 1 ? '/assets/material/pet_stage1.png' : '/assets/material/pet_stage2-4.png'"
      alt="寵物房背景"
      draggable="false"
    >
    <img
      class="pet-sprite"
      :class="stage === 1 ? 'pet-sprite--stage1' : 'pet-sprite--stage2to4'"
      :src="`/assets/material/pet/pet_id_no${stage}.png`"
      :alt="`寵物階段 ${stage}`"
      draggable="false"
    >

    <router-link class="map-btn" to="/student/home" title="返回主頁" aria-label="MAP，返回主頁" />
  </main>
</template>

<style scoped src="@/styles/student/pet.css"></style>
