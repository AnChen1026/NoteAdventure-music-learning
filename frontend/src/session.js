import { reactive } from 'vue'
import { fetchMe } from './api'

// 目前登入者（由路由守衛在進頁前更新）
export const session = reactive({
  role: null,
  user: null
})

export async function refreshSession() {
  const me = await fetchMe()
  session.role = me ? me.role : null
  session.user = me ? me.user : null
  return me
}

export function clearSession() {
  session.role = null
  session.user = null
}
