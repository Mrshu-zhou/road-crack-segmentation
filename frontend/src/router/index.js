import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// 路由表定义
const luyou = [
  {
    path: '/login',
    name: 'denglu',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'yibiaopan',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '数据仪表盘', requiresAuth: true },
  },
  {
    path: '/map',
    name: 'daolu_ditu',
    component: () => import('../views/RoadMap.vue'),
    meta: { title: '道路地图', requiresAuth: true },
  },
  {
    path: '/inspections/new',
    name: 'xinxun_xunjian',
    component: () => import('../views/InspectionNew.vue'),
    meta: { title: '发起巡检', requiresAuth: true, roles: ['user', 'admin'] },
  },
  {
    path: '/segmentation',
    name: 'liefeng_fenge',
    component: () => import('../views/Segmentation.vue'),
    meta: { title: '裂缝分割', requiresAuth: true, roles: ['user', 'admin'] },
  },
  {
    path: '/inspections',
    name: 'xunjian_liebiao',
    component: () => import('../views/InspectionList.vue'),
    meta: { title: '巡检记录', requiresAuth: true },
  },
  {
    path: '/inspections/:id',
    name: 'xunjian_xiangqing',
    component: () => import('../views/InspectionDetail.vue'),
    meta: { title: '巡检详情', requiresAuth: true },
  },
  {
    path: '/workorders',
    name: 'gongdan_liebiao',
    component: () => import('../views/WorkOrderList.vue'),
    meta: { title: '工单管理', requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/roads',
    name: 'daolu_guanli',
    component: () => import('../views/RoadManage.vue'),
    meta: { title: '道路管理', requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/users',
    name: 'yonghu_guanli',
    component: () => import('../views/UserManage.vue'),
    meta: { title: '用户管理', requiresAuth: true, roles: ['admin'] },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes: luyou,
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 设置页面标题
  document.title = to.meta.title
    ? `${to.meta.title} - 道路无人机巡检缺陷检测系统`
    : '道路无人机巡检缺陷检测系统'

  // 登录页直接放行
  if (to.path === '/login') {
    if (authStore.yiDenglu) {
      next('/dashboard')
    } else {
      next()
    }
    return
  }

  // 需要认证的页面检查 token
  if (to.meta.requiresAuth && !authStore.yiDenglu) {
    next('/login')
    return
  }

  // 检查角色权限
  if (to.meta.roles && to.meta.roles.length > 0) {
    const dangqian_juese = authStore.juese
    if (!to.meta.roles.includes(dangqian_juese)) {
      next('/dashboard')
      return
    }
  }

  next()
})

export default router
