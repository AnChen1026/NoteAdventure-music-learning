<script setup>
import { computed } from 'vue'

// 通用表格：未指定 columns 時，用第一筆資料的欄位名稱當表頭
const props = defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, default: null }
})

const headers = computed(() => props.columns || (props.rows.length ? Object.keys(props.rows[0]) : []))

function display(value) {
  if (value === null || value === undefined || value === '') {
    return '—'
  }
  if (typeof value === 'boolean') {
    return value ? '是' : '否'
  }
  return value
}
</script>

<template>
  <div class="t-table-wrap">
    <table class="t-table">
      <thead>
        <tr>
          <th v-for="header in headers" :key="header">{{ header }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in rows" :key="index">
          <td v-for="header in headers" :key="header">{{ display(row[header]) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
