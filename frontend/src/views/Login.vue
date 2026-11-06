<template>
  <div class="denglu_yemian">
    <!-- 道路主题背景图 -->
    <div class="beijing_tu" :style="{ backgroundImage: `url(${beijingTupian})` }"></div>
    <!-- 半透明深色遮罩 -->
    <div class="zhezhao_ceng"></div>

    <!-- 登录卡片 -->
    <div class="denglu_kapian">
      <div class="kapian_toubu">
        <div class="toubu_tubiao">
          <el-icon><Position /></el-icon>
        </div>
        <h1 class="xitong_biaoti">道路无人机巡检</h1>
        <p class="xitong_fubiaoti">缺陷检测智能分析系统</p>
      </div>

      <el-form
        ref="biaodanRef"
        :model="biaodan_shuju"
        :rules="biaodan_guize"
        class="denglu_biaodan"
        size="large"
        @keyup.enter="tijiaoDenglu"
      >
        <el-form-item prop="username">
          <el-input
            v-model="biaodan_shuju.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="biaodan_shuju.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="denglu_anniu"
            :loading="jiazai_zhong"
            @click="tijiaoDenglu"
          >
            {{ jiazai_zhong ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="qiehuan_lianjie">没有账号？请联系后台管理员开通</div>

      <div class="kapian_dibu">
        <span>无人机智能巡检 · AI 缺陷识别 · 工单联动处置</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import beijingTupian from '../assets/login_beijing.jpg'

const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const biaodanRef = ref(null)
// 加载状态
const jiazai_zhong = ref(false)

// 登录表单数据
const biaodan_shuju = reactive({
  username: '',
  password: '',
})

// 表单校验规则
const biaodan_guize = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 提交登录
async function tijiaoDenglu() {
  if (!biaodanRef.value) return
  try {
    await biaodanRef.value.validate()
    jiazai_zhong.value = true
    await authStore.denglu(biaodan_shuju.username, biaodan_shuju.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (cuowu) {
    if (cuowu.message) {
      ElMessage.error(cuowu.message)
    }
  } finally {
    jiazai_zhong.value = false
  }
}
</script>

<style scoped>
.denglu_yemian {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 道路主题背景图 */
.beijing_tu {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: 1;
}

/* 半透明深色遮罩 */
.zhezhao_ceng {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(0, 21, 41, 0.75) 0%, rgba(0, 21, 41, 0.6) 100%);
  z-index: 2;
}

/* 登录卡片 */
.denglu_kapian {
  position: relative;
  z-index: 3;
  width: 420px;
  max-width: 90vw;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 40px 36px 30px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
}

.kapian_toubu {
  text-align: center;
  margin-bottom: 30px;
}

.toubu_tubiao {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #409eff 0%, #1d6fd1 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32px;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.4);
}

.xitong_biaoti {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 8px;
  letter-spacing: 2px;
}

.xitong_fubiaoti {
  font-size: 14px;
  color: #909399;
  margin: 0;
  letter-spacing: 1px;
}

.denglu_biaodan {
  margin-bottom: 0;
}

.denglu_anniu {
  width: 100%;
  height: 44px;
  font-size: 16px;
  letter-spacing: 4px;
  border: none;
  background: linear-gradient(135deg, #409eff 0%, #1d6fd1 100%);
}

.denglu_anniu:hover {
  background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
}

/* 登录注册切换链接 */
.qiehuan_lianjie {
  text-align: center;
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.kapian_dibu {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  font-size: 12px;
  color: #c0c4cc;
  letter-spacing: 1px;
}
</style>
