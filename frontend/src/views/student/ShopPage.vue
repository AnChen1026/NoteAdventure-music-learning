<script setup>
import { onMounted, ref } from 'vue'
import { api } from '@/api'
import { session } from '@/session'
import { ITEM_TYPE_TEXT } from '@/labels'

const coin = ref(session.user ? session.user.total_coin : '—')
const items = ref([])
const loaded = ref(false)
const expanded = ref(null)
const buying = ref(false)
const message = ref('')
const messageType = ref('')

function showMessage(text, type = '') {
  message.value = text
  messageType.value = type
}

function stockText(stock) {
  return stock === null || stock === undefined ? '不限量' : String(stock)
}

function toggle(itemId) {
  expanded.value = expanded.value === itemId ? null : itemId
}

async function loadItems() {
  const { ok, data } = await api(`/api/students/${session.user.student_id}/shop-items`)
  if (!ok) {
    showMessage(data.message || '無法載入商品', 'is-error')
    return
  }
  items.value = data.data || []
  loaded.value = true
}

async function purchase(itemId) {
  buying.value = true
  showMessage('購買中…')
  const { ok, data } = await api(`/api/shop-items/${itemId}/purchase`, { method: 'POST', json: {} })
  buying.value = false
  if (!ok) {
    showMessage(data.message || '購買失敗', 'is-error')
    return
  }
  if (typeof data.total_coin === 'number') {
    coin.value = data.total_coin
  }
  showMessage(data.message || '購買成功', 'is-ok')
  expanded.value = null
  await loadItems()
}

onMounted(loadItems)
</script>

<template>
  <main class="stage" aria-label="學生商店">
    <img class="stage__bg" src="/assets/material/shop.png" alt="Melody Town 商店" draggable="false">

    <section class="shop-panel" aria-label="商品清單">
      <div class="coin-bar">
        <span class="coin-bar__label">持有金幣</span>
        <span class="coin-bar__value">{{ coin }}</span>
      </div>

      <div class="item-list" role="list">
        <article
          v-for="item in items"
          :key="item.item_id"
          class="item-card"
          :class="{ 'is-open': expanded === item.item_id }"
        >
          <button
            type="button"
            class="item-summary"
            :aria-expanded="expanded === item.item_id ? 'true' : 'false'"
            @click="toggle(item.item_id)"
          >
            <span class="item-summary__name">{{ item.item_name }}</span>
            <span class="item-summary__meta">{{ ITEM_TYPE_TEXT[item.item_type] || item.item_type }}</span>
            <span class="item-summary__meta">{{ item.price }} 金幣</span>
            <span class="item-summary__meta">{{ stockText(item.stock) }}</span>
          </button>
          <div class="item-detail">
            <p class="item-detail__desc">{{ (item.description || '').trim() || '（沒有商品說明）' }}</p>
            <button type="button" class="buy-btn" :disabled="buying" @click="purchase(item.item_id)">購買</button>
          </div>
        </article>
      </div>
      <p v-if="loaded && !items.length" class="shop-empty">目前沒有可購買的商品</p>
      <p class="shop-message" :class="messageType" role="status" aria-live="polite">{{ message }}</p>
    </section>

    <router-link class="map-btn" to="/student/home" title="返回主頁" aria-label="MAP，返回主頁" />
  </main>
</template>

<style scoped src="@/styles/student/shop.css"></style>
