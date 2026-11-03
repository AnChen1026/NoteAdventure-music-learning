// ======================================================
// 呼叫 Flask API（老師、學生共用）
// 回傳 { ok, status, data }；連不到伺服器時 status = 0
// ======================================================
export async function api(path, { method = 'GET', json, body, params } = {}) {
  const options = { method, credentials: 'same-origin', headers: {} }
  if (json !== undefined) {
    options.headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(json)
  } else if (body !== undefined) {
    options.body = body
  }

  let url = path
  if (params) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        query.append(key, value)
      }
    })
    const text = query.toString()
    if (text) {
      url += '?' + text
    }
  }

  let response
  try {
    response = await fetch(url, options)
  } catch (error) {
    return { ok: false, status: 0, data: { message: '無法連接伺服器，請確認 Flask 已啟動' } }
  }

  const data = await response.json().catch(() => ({ message: '伺服器回應格式錯誤' }))
  return { ok: response.ok, status: response.status, data }
}

// ======================================================
// 查詢目前登入者：{ role, user } 或 null
// ======================================================
export async function fetchMe() {
  const { ok, data } = await api('/api/me')
  if (!ok || !data || !data.user) {
    return null
  }
  return { role: data.role, user: data.user }
}

export function formatDatetime(value) {
  if (!value) {
    return '無期限'
  }
  return String(value).replace('T', ' ').slice(0, 16)
}
