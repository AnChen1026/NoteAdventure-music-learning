import { createRouter, createWebHistory } from 'vue-router'
import { refreshSession, session } from './session'

import StudentShell from './views/student/StudentShell.vue'
import TeacherLayout from './views/teacher/TeacherLayout.vue'

const routes = [
  { path: '/', redirect: '/student' },

  // ---------- 學生：一頁版（16:9 舞台 + BGM） ----------
  {
    path: '/student',
    component: StudentShell,
    redirect: '/student/home',
    children: [
      { path: 'app', redirect: '/student/home' },
      { path: 'login', component: () => import('./views/student/LoginPage.vue') },
      { path: 'home', component: () => import('./views/student/HomePage.vue'), meta: { role: 'student' } },
      { path: 'practice', component: () => import('./views/student/PracticePage.vue'), meta: { role: 'student' } },
      { path: 'shop', component: () => import('./views/student/ShopPage.vue'), meta: { role: 'student' } },
      { path: 'quests', component: () => import('./views/student/QuestsPage.vue'), meta: { role: 'student' } },
      { path: 'pet', component: () => import('./views/student/PetPage.vue'), meta: { role: 'student' } },
      { path: 'class', component: () => import('./views/student/ClassPage.vue'), meta: { role: 'student' } },
      { path: 'backpack', component: () => import('./views/student/BackpackPage.vue'), meta: { role: 'student' } },
      { path: 'settings', component: () => import('./views/student/SettingsPage.vue'), meta: { role: 'student' } }
    ]
  },

  // ---------- 老師：管理後台 ----------
  { path: '/teacher/login', component: () => import('./views/teacher/TeacherLogin.vue') },
  {
    path: '/teacher',
    component: TeacherLayout,
    redirect: '/teacher/dashboard',
    meta: { role: 'teacher' },
    children: [
      { path: 'dashboard', component: () => import('./views/teacher/DashboardPage.vue'), meta: { title: '首頁' } },
      { path: 'students', component: () => import('./views/teacher/StudentsPage.vue'), meta: { title: '學生列表' } },
      { path: 'students/new', component: () => import('./views/teacher/CreateStudentPage.vue'), meta: { title: '建立學生' } },
      { path: 'students/reset-password', component: () => import('./views/teacher/ResetPasswordPage.vue'), meta: { title: '重設學生密碼' } },
      { path: 'quests', component: () => import('./views/teacher/QuestsPage.vue'), meta: { title: '任務清單' } },
      { path: 'quests/new', component: () => import('./views/teacher/CreateQuestPage.vue'), meta: { title: '新增任務' } },
      { path: 'quests/assign', component: () => import('./views/teacher/AssignQuestPage.vue'), meta: { title: '指派任務' } },
      { path: 'quests/:id/edit', component: () => import('./views/teacher/CreateQuestPage.vue'), meta: { title: '修改任務' } },
      { path: 'uploads', component: () => import('./views/teacher/UploadsPage.vue'), meta: { title: '上傳紀錄' } },
      { path: 'shop', component: () => import('./views/teacher/ShopItemsPage.vue'), meta: { title: '商品清單' } },
      { path: 'shop/new', component: () => import('./views/teacher/CreateShopItemPage.vue'), meta: { title: '新增商品' } },
      { path: 'redeem', component: () => import('./views/teacher/RedeemPage.vue'), meta: { title: '待兌換商品' } },
      { path: 'password', component: () => import('./views/teacher/ChangePasswordPage.vue'), meta: { title: '修改密碼' } }
    ]
  },

  { path: '/:pathMatch(.*)*', redirect: '/student' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 需要登入的頁面：先向 /api/me 確認身分，不符就回到對應登入頁
router.beforeEach(async (to) => {
  const role = to.meta.role
  if (!role) {
    return true
  }
  await refreshSession()
  if (session.role === role) {
    return true
  }
  return role === 'teacher' ? '/teacher/login' : '/student/login'
})

export default router
