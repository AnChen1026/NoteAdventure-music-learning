// ========= 顯示用中文對照（資料庫存英文代碼，介面顯示中文） ===========

export const QUEST_TYPE_TEXT = {
  DAILY: '每日任務',
  WEEKLY: '每週任務',
  HIDDEN: '隱藏任務'
}

export const CONDITION_TEXT = {
  PRACTICE_COUNT: '練習次數',
  PRACTICE_DAYS: '練習天數',
  DISTINCT_SONGS: '不同曲目數',
  CONSECUTIVE_DAYS: '連續練習天數',
  TOTAL_UPLOADS: '累積上傳次數',
  RETURN_AFTER_GAP: '間隔一段時間後再次練習'
}

export const QUEST_STATUS_TEXT = {
  COMPLETED: '已完成',
  ACTIVE: '進行中',
  EXPIRED: '已過期'
}

export const ITEM_TYPE_TEXT = {
  VIRTUAL: '虛擬商品',
  PHYSICAL: '實體商品'
}

export function yesNo(value) {
  return value ? '是' : '否'
}
