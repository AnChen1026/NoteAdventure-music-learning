<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { CONDITION_TEXT, QUEST_TYPE_TEXT } from '@/labels'

// 同一個表單：網址有 :id 時為「修改任務」，否則為「新增任務」
const route = useRoute()
const router = useRouter()
const questId = route.params.id ? Number(route.params.id) : null

const form = reactive({
  quest_name: '',
  quest_type: 'DAILY',
  condition_type: 'PRACTICE_COUNT',
  condition_value: 1,
  reward_xp: 10,
  reward_coin: 5,
  is_once: false
})
const assigned = ref(false)
const ready = ref(!questId)
const loading = ref(false)
const error = ref('')
const warning = ref('')
const notice = ref('')

onMounted(async () => {
  if (!questId) {
    return
  }
  const { ok, data } = await api('/api/quests')
  const quest = ok ? (data.data || []).find((q) => q['任務編號'] === questId) : null
  if (!quest) {
    error.value = ok ? '查無此任務' : data.message || '無法載入任務'
    return
  }
  Object.assign(form, {
    quest_name: quest['任務名稱'],
    quest_type: quest['任務類型'],
    condition_type: quest['任務條件類型'],
    condition_value: quest['任務條件數值'],
    reward_xp: quest['獎勵經驗'],
    reward_coin: quest['獎勵金幣'],
    is_once: !quest['是否為重複任務']
  })
  assigned.value = quest['指派次數'] > 0
  ready.value = true
})

async function submit() {
  error.value = ''
  warning.value = ''
  notice.value = ''
  if (form.quest_name.trim() === '') {
    warning.value = '任務名稱不可空白'
    return
  }
  loading.value = true
  const { ok, data } = await api(questId ? `/api/quests/${questId}` : '/api/quests', {
    method: questId ? 'PUT' : 'POST',
    json: {
      quest_name: form.quest_name.trim(),
      quest_type: form.quest_type,
      condition_type: form.condition_type,
      condition_value: Number(form.condition_value),
      reward_xp: Number(form.reward_xp),
      reward_coin: Number(form.reward_coin),
      is_repeatable: !form.is_once
    }
  })
  loading.value = false
  if (!ok) {
    error.value = data.message || (questId ? '任務修改失敗' : '任務建立失敗')
    return
  }
  if (questId) {
    router.push('/teacher/quests')
    return
  }
  notice.value = data.message || '任務新建成功'
  form.quest_name = ''
}
</script>

<template>
  <div class="t-card">
    <div v-if="assigned" class="t-info">此任務已指派過：不可修改任務類型與條件類型；條件數值與獎勵的修改會套用到尚未完成的指派。</div>
    <form v-if="ready" class="t-form" @submit.prevent="submit">
      <label class="t-field">任務名稱<input v-model="form.quest_name" type="text" maxlength="100"></label>
      <label class="t-field">任務類型
        <select v-model="form.quest_type" :disabled="assigned">
          <option v-for="(label, code) in QUEST_TYPE_TEXT" :key="code" :value="code">{{ label }}</option>
        </select>
      </label>
      <label class="t-field">任務條件
        <select v-model="form.condition_type" :disabled="assigned">
          <option v-for="(label, code) in CONDITION_TEXT" :key="code" :value="code">{{ label }}</option>
        </select>
      </label>
      <label class="t-field">條件數值<input v-model.number="form.condition_value" type="number" min="1" step="1"></label>
      <label class="t-field">獎勵經驗<input v-model.number="form.reward_xp" type="number" min="0" step="1"></label>
      <label class="t-field">獎勵金幣<input v-model.number="form.reward_coin" type="number" min="0" step="1"></label>
      <label class="t-check"><input v-model="form.is_once" type="checkbox">一次性任務（不可重複）</label>
      <div class="t-actions">
        <button class="t-btn t-btn--primary" type="submit" :disabled="loading">{{ questId ? '儲存修改' : '建立任務' }}</button>
        <router-link v-if="questId" class="t-btn" to="/teacher/quests">取消</router-link>
      </div>
    </form>
    <div v-if="warning" class="t-warning">{{ warning }}</div>
    <div v-if="error" class="t-error">{{ error }}</div>
    <div v-if="notice" class="t-notice">{{ notice }}</div>
  </div>
</template>
