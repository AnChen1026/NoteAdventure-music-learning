<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { api } from '@/api'
import { session } from '@/session'
import { pauseBgm, resumeBgm } from '@/student/bgm'

const songName = ref('')
const recording = ref(false)
const stopping = ref(false)
const uploading = ref(false)
const timerText = ref('00:00')
const previewUrl = ref('')
const durationText = ref('')
const durationReady = ref(false)
const message = ref('輸入曲名後開始錄音，錄完可試聽再上傳')
const messageType = ref('')
const songInput = ref(null)
const previewAudio = ref(null)

let mediaStream = null
let mediaRecorder = null
let chunks = []
let recordedBlob = null
let audioDuration = 0
let timerId = null
let startedAt = 0

function showMessage(text, type = '') {
  message.value = text
  messageType.value = type
}

function formatTime(totalSeconds) {
  const sec = Math.max(0, Math.floor(totalSeconds))
  return String(Math.floor(sec / 60)).padStart(2, '0') + ':' + String(sec % 60).padStart(2, '0')
}

function pickMimeType() {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus']
  if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) {
    return ''
  }
  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || ''
}

function extensionForMime(mime) {
  if (mime.includes('mp4')) {
    return 'm4a'
  }
  if (mime.includes('ogg')) {
    return 'ogg'
  }
  return 'webm'
}

function clearPreview() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
}

function resetRecording() {
  chunks = []
  recordedBlob = null
  audioDuration = 0
  clearPreview()
  timerText.value = '00:00'
  durationText.value = ''
  durationReady.value = false
}

function stopTimer() {
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
}

function stopStream() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop())
    mediaStream = null
  }
}

function onRecorderStop(mimeType) {
  stopTimer()
  stopStream()
  recording.value = false
  stopping.value = false

  recordedBlob = new Blob(chunks, { type: mediaRecorder.mimeType || mimeType || 'audio/webm' })
  clearPreview()
  previewUrl.value = URL.createObjectURL(recordedBlob)

  // 以實際音檔長度為準；讀不到時用計時秒數
  audioDuration = Math.max(1, Math.round((Date.now() - startedAt) / 1000))
  durationText.value = '錄音長度：約 ' + audioDuration + ' 秒（讀取精確長度中…）'
  durationReady.value = false
  // 部分瀏覽器 webm 暫時無 duration，給短延遲後仍允許上傳
  setTimeout(() => {
    if (!durationReady.value && recordedBlob) {
      durationText.value = '錄音長度：約 ' + audioDuration + ' 秒'
      durationReady.value = true
    }
  }, 800)

  showMessage('請試聽確認，沒問題再按「確認上傳」', 'is-ok')
  resumeBgm()
}

function onPreviewMeta() {
  const audioEl = previewAudio.value
  if (audioEl && audioEl.duration && isFinite(audioEl.duration) && audioEl.duration > 0) {
    audioDuration = Math.max(1, Math.round(audioEl.duration))
  }
  durationText.value = '錄音長度：' + audioDuration + ' 秒'
  durationReady.value = audioDuration > 0
}

async function startRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showMessage('此瀏覽器不支援麥克風錄音', 'is-error')
    return
  }
  if (!window.MediaRecorder) {
    showMessage('此瀏覽器不支援錄音功能', 'is-error')
    return
  }

  resetRecording()
  showMessage('請允許使用麥克風…')
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch (error) {
    showMessage('無法取得麥克風權限', 'is-error')
    return
  }

  const mimeType = pickMimeType()
  try {
    mediaRecorder = mimeType ? new MediaRecorder(mediaStream, { mimeType }) : new MediaRecorder(mediaStream)
  } catch (error) {
    showMessage('無法開始錄音', 'is-error')
    stopStream()
    return
  }

  mediaRecorder.addEventListener('dataavailable', (event) => {
    if (event.data && event.data.size > 0) {
      chunks.push(event.data)
    }
  })
  mediaRecorder.addEventListener('stop', () => onRecorderStop(mimeType))

  mediaRecorder.start()
  recording.value = true
  startedAt = Date.now()
  stopTimer()
  timerId = setInterval(() => {
    timerText.value = formatTime((Date.now() - startedAt) / 1000)
  }, 200)
  showMessage('錄音中…')
  // 錄音時暫停 BGM，避免錄進背景音樂
  pauseBgm()
}

function stopRecording() {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') {
    return
  }
  stopping.value = true
  mediaRecorder.stop()
}

function onRecordClick() {
  if (recording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

function rerecord() {
  resetRecording()
  showMessage('請重新錄音')
  startRecording()
}

async function upload() {
  const name = songName.value.trim()
  if (name === '') {
    showMessage('請輸入曲目名稱', 'is-error')
    songInput.value && songInput.value.focus()
    return
  }
  if (!recordedBlob) {
    showMessage('請先完成錄音', 'is-error')
    return
  }
  if (audioDuration <= 0) {
    showMessage('錄音時間太短，請重新錄製', 'is-error')
    return
  }

  uploading.value = true
  showMessage('上傳中…')
  const mime = recordedBlob.type || 'audio/webm'
  const form = new FormData()
  form.append('song_name', name)
  form.append('audio_duration', String(audioDuration))
  form.append('audio', recordedBlob, 'practice.' + extensionForMime(mime))

  const { ok, data } = await api(`/api/students/${session.user.student_id}/practice-uploads`, {
    method: 'POST',
    body: form
  })
  uploading.value = false

  if (!ok) {
    showMessage(data.message || '上傳失敗', 'is-error')
    return
  }

  let text = data.message || '練習上傳成功'
  const rewards = data.rewards || []
  if (rewards.length > 0) {
    const parts = rewards.map((r) => `${r.quest_name}（+${r.reward_xp} XP、+${r.reward_coin} 金幣）`)
    text += '；完成任務：' + parts.join('、')
  }
  showMessage(text, 'is-ok')
  resetRecording()
}

// 離開琴房時停止麥克風並恢復 BGM
onBeforeUnmount(() => {
  stopTimer()
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  stopStream()
  clearPreview()
  resumeBgm()
})
</script>

<template>
  <main class="stage" aria-label="學生琴房">
    <img class="stage__bg" src="/assets/material/practice.png" alt="Melody Town 琴房" draggable="false">

    <section class="practice-panel" aria-label="練習錄音">
      <h1 class="practice-panel__title">琴房</h1>

      <label class="field" for="song-name">
        <span class="field__label">曲目名稱</span>
        <input
          id="song-name"
          ref="songInput"
          v-model="songName"
          class="field__input"
          type="text"
          maxlength="100"
          placeholder="請輸入曲名"
          autocomplete="off"
        >
      </label>

      <div class="record-row">
        <button
          type="button"
          class="action-btn action-btn--record"
          :class="{ 'is-recording': recording }"
          :disabled="stopping || uploading"
          @click="onRecordClick"
        >{{ recording ? '停止錄音' : '開始錄音' }}</button>
        <span class="record-timer" :class="{ 'is-recording': recording }" aria-live="polite">{{ timerText }}</span>
      </div>

      <div v-if="previewUrl" class="preview-box">
        <p class="preview-box__label">試聽確認</p>
        <audio ref="previewAudio" class="preview-audio" controls :src="previewUrl" @loadedmetadata="onPreviewMeta"></audio>
        <p class="duration-text">{{ durationText }}</p>
      </div>

      <div class="btn-row">
        <button
          v-if="previewUrl"
          type="button"
          class="action-btn action-btn--secondary"
          :disabled="uploading"
          @click="rerecord"
        >重新錄音</button>
        <button
          v-if="previewUrl"
          type="button"
          class="action-btn action-btn--upload"
          :disabled="!durationReady || uploading"
          @click="upload"
        >確認上傳</button>
      </div>

      <p class="practice-message" :class="messageType" role="status" aria-live="polite">{{ message }}</p>
    </section>

    <router-link class="map-btn" to="/student/home" title="返回主頁" aria-label="MAP，返回主頁" />
  </main>
</template>

<style scoped src="@/styles/student/practice.css"></style>
