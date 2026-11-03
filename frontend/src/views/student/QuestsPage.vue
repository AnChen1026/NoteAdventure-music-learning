<script setup>
import { onMounted, ref } from 'vue'
import { api, formatDatetime } from '@/api'
import { session } from '@/session'
import { CONDITION_TEXT, QUEST_STATUS_TEXT, QUEST_TYPE_TEXT } from '@/labels'

const quests = ref([])
const loaded = ref(false)
const emptyText = ref('目前沒有任務')
const message = ref('')
const expanded = ref(null)

function percent(current, target) {
  if (!target || target <= 0) {
    return 0
  }
  return Math.min(100, Math.round((current / target) * 100))
}

function toggle(index) {
  expanded.value = expanded.value === index ? null : index
}

onMounted(async () => {
  const { ok, data } = await api(`/api/students/${session.user.student_id}/quests`)
  if (!ok) {
    message.value = data.message || '無法載入任務'
    return
  }
  quests.value = data.data || []
  if (!quests.value.length && data.message) {
    emptyText.value = data.message
  }
  loaded.value = true
})
</script>

<template>
  <main class="stage" aria-label="學生任務欄">
    <img class="stage__bg" src="/assets/material/quest.png" alt="Melody Town 任務欄" draggable="false">

    <section class="quest-panel" aria-label="任務清單">
      <h1 class="quest-panel__title">任務欄</h1>
      <div class="quest-list" role="list">
        <article
          v-for="(quest, index) in quests"
          :key="index"
          class="quest-card"
          :class="{ 'is-open': expanded === index }"
        >
          <button
            type="button"
            class="quest-summary"
            :aria-expanded="expanded === index ? 'true' : 'false'"
            @click="toggle(index)"
          >
            <span class="quest-summary__name">{{ quest.quest_name }}</span>
            <span class="quest-summary__meta">{{ QUEST_TYPE_TEXT[quest.quest_type] || quest.quest_type }}</span>
            <span class="quest-summary__meta">{{ quest.progress_value || 0 }} / {{ quest.condition_value || 0 }}</span>
            <span class="quest-summary__meta">{{ QUEST_STATUS_TEXT[quest.quest_status] || quest.quest_status }}</span>
          </button>
          <div class="quest-detail">
            <p>條件：{{ CONDITION_TEXT[quest.condition_type] || quest.condition_type }} {{ quest.condition_value }}</p>
            <p>獎勵：經驗 {{ quest.reward_xp }}／金幣 {{ quest.reward_coin }}</p>
            <p>到期時間：{{ formatDatetime(quest.expires_at) }}</p>
            <div class="progress" aria-hidden="true">
              <div class="progress__bar" :style="{ width: percent(quest.progress_value || 0, quest.condition_value) + '%' }"></div>
            </div>
          </div>
        </article>
      </div>
      <p v-if="loaded && !quests.length" class="quest-empty">{{ emptyText }}</p>
      <p class="quest-message" role="status" aria-live="polite">{{ message }}</p>
    </section>

    <router-link class="map-btn" to="/student/home" title="返回主頁" aria-label="MAP，返回主頁" />
  </main>
</template>

<style scoped src="@/styles/student/quests.css"></style>
