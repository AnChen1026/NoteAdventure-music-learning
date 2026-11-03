<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { bgmPlaying, ensureBgm, stopBgm, toggleBgm } from '@/student/bgm'

// 外殼：BGM／橫放提示／全螢幕／捲動鎖定；功能頁在 router-view 內切換
const shell = ref(null)
let lastTap = 0

function isTypingField(el) {
  if (!el || !el.tagName) {
    return false
  }
  const tag = el.tagName.toUpperCase()
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el.isContentEditable
}

function resetScroll() {
  window.scrollTo(0, 0)
  document.documentElement.scrollTop = 0
  document.body.scrollTop = 0
}

// 手機鍵盤收起後把畫面拉回
function onFocusOut(event) {
  if (!isTypingField(event.target)) {
    return
  }
  setTimeout(() => {
    if (isTypingField(document.activeElement)) {
      return
    }
    resetScroll()
    setTimeout(resetScroll, 50)
    setTimeout(resetScroll, 300)
  }, 0)
}

function onScroll() {
  if (window.scrollX || window.scrollY) {
    resetScroll()
  }
}

// 鎖住外層頁面捲動（內層清單仍可滾）
function lockPageScroll(event) {
  const target = event.target
  if (!target || !target.closest) {
    event.preventDefault()
    return
  }
  if (target.closest('.rotate-gate') || isTypingField(target) || target.closest('label')) {
    return
  }
  const scrollable = target.closest(
    '.item-list, .quest-list, .practice-panel, .settings-panel, .shop-panel, .quest-panel, .board-track, .backpack-grid'
  )
  if (scrollable && scrollable.scrollHeight > scrollable.clientHeight + 1) {
    return
  }
  event.preventDefault()
}

function toggleFullscreen() {
  const el = document.documentElement
  try {
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
      if (el.requestFullscreen) {
        el.requestFullscreen()
      } else if (el.webkitRequestFullscreen) {
        el.webkitRequestFullscreen()
      }
    } else if (document.exitFullscreen) {
      document.exitFullscreen()
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen()
    }
  } catch (error) {
    // 行動瀏覽器不支援時略過
  }
}

function onTouchEnd(event) {
  const now = Date.now()
  if (now - lastTap < 300) {
    event.preventDefault()
    toggleFullscreen()
    lastTap = 0
  } else {
    lastTap = now
  }
}

// 瀏覽器常擋自動播放：使用者第一次點擊時再試
function onPointerDown() {
  ensureBgm()
}

onMounted(() => {
  document.documentElement.classList.add('na-student')
  document.addEventListener('focusout', onFocusOut)
  document.addEventListener('touchmove', lockPageScroll, { passive: false })
  document.addEventListener('pointerdown', onPointerDown, { passive: true })
  window.addEventListener('scroll', onScroll, { passive: true })
  ensureBgm()
})

onBeforeUnmount(() => {
  document.documentElement.classList.remove('na-student')
  document.removeEventListener('focusout', onFocusOut)
  document.removeEventListener('touchmove', lockPageScroll)
  document.removeEventListener('pointerdown', onPointerDown)
  window.removeEventListener('scroll', onScroll)
  stopBgm()
})
</script>

<template>
  <main
    ref="shell"
    class="na-shell"
    aria-label="學生網頁"
    @dblclick="toggleFullscreen"
    @touchend="onTouchEnd"
  >
    <router-view v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>

    <button
      type="button"
      class="bgm-toggle"
      :class="{ 'is-off': !bgmPlaying }"
      :aria-pressed="bgmPlaying ? 'true' : 'false'"
      :title="bgmPlaying ? '關閉背景音樂' : '開啟背景音樂'"
      :aria-label="bgmPlaying ? '關閉背景音樂' : '開啟背景音樂'"
      @click.stop.prevent="toggleBgm"
      @dblclick.stop
    >{{ bgmPlaying ? '♪' : '🔇' }}</button>
  </main>

  <div class="rotate-gate" role="dialog" aria-live="polite" aria-label="請將裝置橫向放置">
    <div class="rotate-gate__icon" aria-hidden="true"></div>
    <p class="rotate-gate__title">請將裝置橫放</p>
    <p class="rotate-gate__hint">手機或平板請轉成橫向後，即可操作 Melody Town</p>
  </div>
</template>

<style src="@/styles/student/shell.css"></style>
