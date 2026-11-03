<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { api } from '@/api'

// 佈告欄：兩廳院近一個月音樂節目（每 3 秒自動橫向切換）
const AUTO_MS = 3000

const programs = ref([])
const notice = ref({ title: '節目載入中…', detail: '正在向兩廳院取得近一個月音樂節目' })
const index = ref(0)
const track = ref(null)
let autoTimer = null

function dateText(item) {
  return item.start_date === item.end_date
    ? item.start_date || ''
    : (item.start_date || '') + ' ~ ' + (item.end_date || '')
}

function goTo(next, smooth = true) {
  if (!track.value || !programs.value.length) {
    return
  }
  const count = programs.value.length
  index.value = (next + count) % count
  track.value.scrollTo({
    left: track.value.clientWidth * index.value,
    behavior: smooth ? 'smooth' : 'auto'
  })
}

function stopAuto() {
  if (autoTimer !== null) {
    clearInterval(autoTimer)
    autoTimer = null
  }
}

function startAuto() {
  stopAuto()
  if (programs.value.length > 1) {
    autoTimer = setInterval(() => goTo(index.value + 1), AUTO_MS)
  }
}

function onDot(i) {
  goTo(i)
  startAuto()
}

function onScroll() {
  requestAnimationFrame(() => {
    if (!track.value || !programs.value.length) {
      return
    }
    const next = Math.round(track.value.scrollLeft / (track.value.clientWidth || 1))
    index.value = Math.max(0, Math.min(programs.value.length - 1, next))
  })
}

onMounted(async () => {
  const { ok, status, data } = await api('/api/class/ntch-programs')
  if (!ok) {
    notice.value = status === 0
      ? { title: '節目載入失敗', detail: '請確認網路後重新整理' }
      : { title: '目前無法取得節目', detail: data.message || '請稍後再重新整理頁面' }
    return
  }
  const items = data.data || []
  if (!items.length) {
    notice.value = { title: '近一個月暫無音樂相關節目', detail: '' }
    return
  }
  programs.value = items
  startAuto()
})

onBeforeUnmount(stopAuto)
</script>

<template>
  <main class="stage" aria-label="學生教室">
    <img class="stage__bg" src="/assets/material/class.png" alt="Melody Town 教室" draggable="false">

    <section class="board-panel" aria-label="兩廳院音樂節目看板">
      <h1 class="board-panel__title">兩廳院音樂節目</h1>

      <div class="board-carousel">
        <div
          ref="track"
          class="board-track"
          tabindex="0"
          aria-live="polite"
          @scroll="onScroll"
          @mouseenter="stopAuto"
          @mouseleave="startAuto"
        >
          <template v-if="programs.length">
            <a
              v-for="item in programs"
              :key="item.url || item.title"
              class="board-card"
              :href="item.url || '#'"
              target="_blank"
              rel="noopener noreferrer"
              :aria-label="(item.title || '節目') + '，另開兩廳院頁面'"
            >
              <img v-if="item.cover_url" class="board-card__poster" :src="item.cover_url" alt="" loading="lazy">
              <div v-else class="board-card__poster board-card__poster--empty">無海報</div>
              <div class="board-card__body">
                <h2 class="board-card__title">{{ item.title || '未命名節目' }}</h2>
                <p class="board-card__meta">{{ dateText(item) }}<template v-if="item.category"> ｜ {{ item.category }}</template></p>
                <p class="board-card__brief">{{ item.brief || '' }}</p>
              </div>
            </a>
          </template>
          <div v-else class="board-card">
            <div class="board-card__poster board-card__poster--empty">看板</div>
            <div class="board-card__body">
              <h2 class="board-card__title">{{ notice.title }}</h2>
              <p v-if="notice.detail" class="board-card__brief">{{ notice.detail }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="board-dots" aria-hidden="true">
        <button
          v-for="(item, i) in programs"
          :key="i"
          type="button"
          class="board-dot"
          :class="{ 'is-active': i === index }"
          :aria-label="`第 ${i + 1} 則`"
          @click="onDot(i)"
        ></button>
      </div>
    </section>

    <router-link class="map-btn" to="/student/home" title="返回主頁" aria-label="MAP，返回主頁" />
  </main>
</template>

<style scoped src="@/styles/student/class.css"></style>
