<template>
  <!-- 登录页不显示导航布局 -->
  <router-view v-if="shiFouDengluYe" />

  <!-- 已认证页面显示导航布局 -->
  <el-container v-else class="app_buju">
    <!-- 侧边导航栏 -->
    <el-aside :width="zhedie ? '64px' : '220px'" class="cebian_lan">
      <div class="logo_qu">
        <el-icon class="logo_tubiao"><Position /></el-icon>
        <span v-show="!zhedie" class="logo_wenzi">道路巡检系统</span>
      </div>
      <el-menu
        :default-active="dangqianLujing"
        :collapse="zhedie"
        :collapse-transition="false"
        background-color="#001529"
        text-color="#b7c0cd"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/map" v-if="nengFangwen(['user', 'admin'])">
          <el-icon><MapLocation /></el-icon>
          <template #title>道路地图</template>
        </el-menu-item>
        <el-menu-item index="/inspections/new" v-if="nengFangwen(['user', 'admin'])">
          <el-icon><Upload /></el-icon>
          <template #title>发起巡检</template>
        </el-menu-item>
        <el-menu-item index="/segmentation" v-if="nengFangwen(['user', 'admin'])">
          <el-icon><Aim /></el-icon>
          <template #title>裂缝分割</template>
        </el-menu-item>
        <el-menu-item index="/inspections">
          <el-icon><Picture /></el-icon>
          <template #title>巡检记录</template>
        </el-menu-item>
        <el-menu-item index="/workorders" v-if="nengFangwen(['admin'])">
          <el-icon><Tickets /></el-icon>
          <template #title>工单管理</template>
        </el-menu-item>
        <el-sub-menu index="guanli" v-if="nengFangwen(['admin'])">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/admin/roads">
            <el-icon><Location /></el-icon>
            <template #title>道路管理</template>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- 右侧主内容区 -->
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="dingbu_lan">
        <div class="dingbu_zuo">
          <el-icon class="zhedie_an" @click="zhedie = !zhedie">
            <Fold v-if="!zhedie" />
            <Expand v-else />
          </el-icon>
          <span class="yemian_biaoti">{{ yemianBiaoti }}</span>
        </div>
        <div class="dingbu_you">
          <el-dropdown @command="xialaChuli">
            <span class="yonghu_xinxi">
              <el-avatar :size="32" class="yonghu_touxiang">
                {{ yonghuMingShouZi }}
              </el-avatar>
              <span class="yonghu_ming">{{ authStore.yonghuMing }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  角色：{{ jueseMingcheng }}
                </el-dropdown-item>
                <el-dropdown-item divided command="dengchu">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区域 -->
      <el-main class="zhuti_qu">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 侧边栏折叠状态
const zhedie = ref(false)

// 是否为登录页
const shiFouDengluYe = computed(() => route.path === '/login')

// 当前路径（用于菜单高亮）
const dangqianLujing = computed(() => route.path)

// 页面标题映射
const biaoti_map = {
  '/dashboard': '数据仪表盘',
  '/map': '道路地图',
  '/inspections/new': '发起巡检',
  '/segmentation': '裂缝分割',
  '/inspections': '巡检记录',
  '/inspections/detail': '巡检详情',
  '/workorders': '工单管理',
  '/admin/roads': '道路管理',
  '/admin/users': '用户管理',
}

// 当前页面标题
const yemianBiaoti = computed(() => {
  if (route.path.startsWith('/inspections/') && route.path !== '/inspections/new') {
    return '巡检详情'
  }
  return biaoti_map[route.path] || '道路无人机巡检缺陷检测系统'
})

// 用户名首字母（用于头像）
const yonghuMingShouZi = computed(() => {
  const ming = authStore.yonghuMing
  return ming ? ming.charAt(0).toUpperCase() : 'U'
})

// 角色中文名称
const jueseMingcheng = computed(() => {
  const map = { user: '巡检员', admin: '管理员' }
  return map[authStore.juese] || authStore.juese
})

// 判断当前用户是否能访问指定角色页面
function nengFangwen(jueseLiebiao) {
  return jueseLiebiao.includes(authStore.juese)
}

// 下拉菜单处理
async function xialaChuli(command) {
  if (command === 'dengchu') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      })
      authStore.dengchu()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      // 取消退出
    }
  }
}
</script>

<style scoped>
.app_buju {
  height: 100vh;
}

/* 侧边导航栏样式 */
.cebian_lan {
  background-color: #001529;
  transition: width 0.3s;
  overflow-x: hidden;
}

.logo_qu {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  border-bottom: 1px solid #1d2b3f;
}

.logo_tubiao {
  font-size: 24px;
  color: #409eff;
}

.logo_wenzi {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

/* 覆盖 element-plus 菜单边框 */
.cebian_lan .el-menu {
  border-right: none;
}

/* 顶部导航栏样式 */
.dingbu_lan {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0 20px;
}

.dingbu_zuo {
  display: flex;
  align-items: center;
  gap: 16px;
}

.zhedie_an {
  font-size: 20px;
  cursor: pointer;
  color: #5a5e66;
  transition: color 0.2s;
}

.zhedie_an:hover {
  color: #409eff;
}

.yemian_biaoti {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.dingbu_you {
  display: flex;
  align-items: center;
}

.yonghu_xinxi {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #303133;
}

.yonghu_touxiang {
  background: #409eff;
  color: #fff;
  font-weight: 600;
}

.yonghu_ming {
  font-size: 14px;
}

/* 主内容区 */
.zhuti_qu {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
