import { ref } from 'vue'

// ======================================================
// 學生端背景音樂（整個一頁版共用同一個 audio，換頁不中斷）
// ======================================================
const STORAGE_KEY = 'na_bgm_enabled'
const TIME_KEY = 'na_bgm_time'

let audio = null
let pausedByApp = false
let lastSave = 0

export const bgmPlaying = ref(false)

function readStorage(key) {
  try {
    return sessionStorage.getItem(key)
  } catch (error) {
    return null
  }
}

function writeStorage(key, value) {
  try {
    sessionStorage.setItem(key, value)
  } catch (error) {
    // 無痕模式等情況略過
  }
}

function isEnabled() {
  const saved = readStorage(STORAGE_KEY)
  return saved === null ? true : saved === '1'
}

function saveTime() {
  if (audio && audio.currentTime && isFinite(audio.currentTime)) {
    writeStorage(TIME_KEY, String(audio.currentTime))
  }
}

function syncState() {
  bgmPlaying.value = !!audio && isEnabled() && !audio.paused
}

function getAudio() {
  if (audio) {
    return audio
  }
  audio = new Audio('/assets/material/bgm/bgm.mp3')
  audio.loop = true
  audio.preload = 'auto'
  audio.volume = 0.32
  audio.setAttribute('playsinline', '')

  const saved = parseFloat(readStorage(TIME_KEY) || '0')
  if (saved > 0 && isFinite(saved)) {
    audio.addEventListener('loadedmetadata', () => {
      try {
        audio.currentTime = saved
      } catch (error) {
        // ignore
      }
    }, { once: true })
  }

  audio.addEventListener('timeupdate', () => {
    // 節流：約每 2 秒記一次進度
    if (Date.now() - lastSave > 2000) {
      lastSave = Date.now()
      saveTime()
    }
  })
  audio.addEventListener('play', syncState)
  audio.addEventListener('pause', syncState)
  return audio
}

// 若已在播就不動，避免換頁像「斷掉重來」；瀏覽器擋自動播放時等使用者點擊再試
export function ensureBgm() {
  const el = getAudio()
  if (!isEnabled() || pausedByApp || !el.paused) {
    syncState()
    return
  }
  el.play().catch(() => {}).finally(syncState)
}

// 琴房錄音時暫停，避免錄進背景音樂
export function pauseBgm() {
  pausedByApp = true
  saveTime()
  getAudio().pause()
}

export function resumeBgm() {
  pausedByApp = false
  ensureBgm()
}

export function toggleBgm() {
  const el = getAudio()
  if (isEnabled() && !el.paused) {
    writeStorage(STORAGE_KEY, '0')
    saveTime()
    el.pause()
    return
  }
  writeStorage(STORAGE_KEY, '1')
  pausedByApp = false
  ensureBgm()
}

// 離開學生端（例如切到老師後台）時停止
export function stopBgm() {
  if (audio) {
    saveTime()
    audio.pause()
  }
}
