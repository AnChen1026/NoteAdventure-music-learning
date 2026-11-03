<script setup>
import { onMounted, ref } from 'vue'
import { api } from '@/api'
import { CONDITION_TEXT, QUEST_TYPE_TEXT, yesNo } from '@/labels'

const error = ref('')
const empty = ref('')
const notice = ref('')
const quests = ref([])
const busyId = ref(null)

async function load() {
  const { ok, data } = await api('/api/quests')
  if (!ok) {
    error.value = data.message || '無法載入任務'
    return
  }
  quests.value = data.data || []
  empty.value = quests.value.length ? '' : data.message || '無任務資料'
}

// 啟用／停用、刪除共用：送出後顯示訊息並重新載入
async function run(questId, path, options) {
  busyId.value = questId
  error.value = ''
  notice.value = ''
  const { ok, data } = await api(path, options)
  busyId.value = null
  if (!ok) {
    error.value = data.message || '操作失敗'
    return
  }
  notice.value = data.message || '操作完成'
  await load()
}

function toggleActive(q) {
  run(q['任務編號'], `/api/quests/${q['任務編號']}/active`, {
    method: 'PATCH',
    json: { is_active: !q['任務是否啟用'] }
  })
}

function remove(q) {
  if (!window.confirm(`確定刪除任務「${q['任務名稱']}」？`)) {
    return
  }
  run(q['任務編號'], `/api/quests/${q['任務編號']}`, { method: 'DELETE' })
}

onMounted(load)
</script>

<template>
  <div v-if="notice" class="t-notice">{{ notice }}</div>
  <div v-if="error" class="t-error">{{ error }}</div>
  <div v-if="empty" class="t-info">{{ empty }}</div>
  <div v-if="quests.length" class="t-table-wrap">
    <table class="t-table">
      <thead>
        <tr>
          <th>任務編號</th>
          <th>任務名稱</th>
          <th>任務類型</th>
          <th>任務條件</th>
          <th>條件數值</th>
          <th>獎勵經驗</th>
          <th>獎勵金幣</th>
          <th>可重複</th>
          <th>指派次數</th>
          <th>啟用狀態</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="q in quests" :key="q['任務編號']">
          <td>{{ q['任務編號'] }}</td>
          <td>{{ q['任務名稱'] }}</td>
          <td>{{ QUEST_TYPE_TEXT[q['任務類型']] || q['任務類型'] }}</td>
          <td>{{ CONDITION_TEXT[q['任務條件類型']] || q['任務條件類型'] }}</td>
          <td>{{ q['任務條件數值'] }}</td>
          <td>{{ q['獎勵經驗'] }}</td>
          <td>{{ q['獎勵金幣'] }}</td>
          <td>{{ yesNo(q['是否為重複任務']) }}</td>
          <td>{{ q['指派次數'] }}</td>
          <td>{{ q['任務是否啟用'] ? '啟用中' : '已停用' }}</td>
          <td class="t-actions">
            <router-link class="t-btn" :to="`/teacher/quests/${q['任務編號']}/edit`">修改</router-link>
            <button type="button" class="t-btn" :disabled="busyId === q['任務編號']" @click="toggleActive(q)">
              {{ q['任務是否啟用'] ? '停用' : '啟用' }}
            </button>
            <button
              type="button"
              class="t-btn"
              :disabled="busyId === q['任務編號'] || q['指派次數'] > 0"
              :title="q['指派次數'] > 0 ? '已有指派紀錄，請改用停用' : ''"
              @click="remove(q)"
            >刪除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
