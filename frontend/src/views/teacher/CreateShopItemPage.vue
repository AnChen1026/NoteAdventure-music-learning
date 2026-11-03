<script setup>
import { reactive, ref } from 'vue'
import { api } from '@/api'
import { ITEM_TYPE_TEXT } from '@/labels'

const form = reactive({
  item_name: '',
  item_type: 'VIRTUAL',
  price: 10,
  unlimited: true,
  stock: 1,
  description: ''
})
const loading = ref(false)
const error = ref('')
const warning = ref('')
const notice = ref('')

async function submit() {
  error.value = ''
  warning.value = ''
  notice.value = ''
  if (form.item_name.trim() === '') {
    warning.value = '商品名稱不可空白'
    return
  }
  loading.value = true
  const { ok, data } = await api('/api/shop-items', {
    method: 'POST',
    json: {
      item_name: form.item_name.trim(),
      item_type: form.item_type,
      price: Number(form.price),
      stock: form.unlimited ? null : Number(form.stock),
      description: form.description.trim() || null
    }
  })
  loading.value = false
  if (!ok) {
    error.value = data.message || '商品新增失敗'
    return
  }
  notice.value = data.message || '商品新增成功'
  form.item_name = ''
  form.description = ''
}
</script>

<template>
  <div class="t-card">
    <form class="t-form" @submit.prevent="submit">
      <label class="t-field">商品名稱<input v-model="form.item_name" type="text" maxlength="100"></label>
      <label class="t-field">商品類型
        <select v-model="form.item_type">
          <option v-for="(label, code) in ITEM_TYPE_TEXT" :key="code" :value="code">{{ label }}</option>
        </select>
      </label>
      <label class="t-field">價格（金幣）<input v-model.number="form.price" type="number" min="0" step="1"></label>
      <label class="t-check"><input v-model="form.unlimited" type="checkbox">不限量庫存</label>
      <label v-if="!form.unlimited" class="t-field">庫存數量<input v-model.number="form.stock" type="number" min="0" step="1"></label>
      <label class="t-field">商品說明（可留空）<textarea v-model="form.description" rows="3" maxlength="255"></textarea></label>
      <button class="t-btn t-btn--primary" type="submit" :disabled="loading">建立商品</button>
    </form>
    <div v-if="warning" class="t-warning">{{ warning }}</div>
    <div v-if="error" class="t-error">{{ error }}</div>
    <div v-if="notice" class="t-notice">{{ notice }}</div>
  </div>
</template>
