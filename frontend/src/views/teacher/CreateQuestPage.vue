<script setup>
import { reactive, ref } from 'vue'
import { api } from '@/api'
import { CONDITION_TEXT, QUEST_TYPE_TEXT } from '@/labels'

const form = reactive({
  quest_name: '',
  quest_type: 'DAILY',
  condition_type: 'PRACTICE_COUNT',
  condition_value: 1,
  reward_xp: 10,
  reward_coin: 5,
  is_once: false
})
const loading = ref(false)
const error = ref('')
const warning = ref('')
const notice = ref('')

async function submit() {
  error.value = ''
  warning.value = ''
  notice.value = ''
  if (form.quest_name.trim() === '') {
    warning.value = '任務名稱不可空白'
    return
  }
  loading.value = true
  const { ok, data } = await api('/api/quests', {
    method: 'POST',
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
    error.value = data.message || '任務建立失敗'
    return
  }
  notice.value = data.message || '任務新建成功'
  form.quest_name = ''
}
</script>

<template>
  <div class="t-card">
    <form class="t-form" @submit.prevent="submit">
      <label class="t-field">任務名稱<input v-model="form.quest_name" type="text" maxlength="100"></label>
      <label class="t-field">任務類型
        <select v-model="form.quest_type">
          <option v-for="(label, code) in QUEST_TYPE_TEXT" :key="code" :value="code">{{ label }}</option>
        </select>
      </label>
      <label class="t-field">任務條件
        <select v-model="form.condition_type">
          <option v-for="(label, code) in CONDITION_TEXT" :key="code" :value="code">{{ label }}</option>
        </select>
      </label>
      <label class="t-field">條件數值<input v-model.number="form.condition_value" type="number" min="1" step="1"></label>
      <label class="t-field">獎勵經驗<input v-model.number="form.reward_xp" type="number" min="0" step="1"></label>
      <label class="t-field">獎勵金幣<input v-model.number="form.reward_coin" type="number" min="0" step="1"></label>
      <label class="t-check"><input v-model="form.is_once" type="checkbox">一次性任務（不可重複）</label>
      <button class="t-btn t-btn--primary" type="submit" :disabled="loading">建立任務</button>
    </form>
    <div v-if="warning" class="t-warning">{{ warning }}</div>
    <div v-if="error" class="t-error">{{ error }}</div>
    <div v-if="notice" class="t-notice">{{ notice }}</div>
  </div>
</template>
