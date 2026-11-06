<template>
  <div class="yonghu_yemian">
    <el-card shadow="hover">
      <!-- 顶部操作栏 -->
      <div class="caozuo_lan">
        <el-form :inline="true" :model="shaixuan_tiaojian">
          <el-form-item label="用户搜索">
            <el-input
              v-model="shaixuan_tiaojian.guanjianci"
              placeholder="输入用户名/姓名搜索"
              clearable
              style="width: 240px"
            />
          </el-form-item>
        </el-form>
        <el-button type="primary" :icon="Plus" @click="dakaiXinjian">新增用户</el-button>
      </div>

      <!-- 数据表格 -->
      <el-table :data="guolv_liebiao" v-loading="jiazai_zhong" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="real_name" label="真实姓名" min-width="120">
          <template #default="{ row }">
            {{ row.real_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="jueseLeixing(row.role)" effect="dark" size="small">
              {{ jueseWenzi(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140" align="center">
          <template #default="{ row }">
            {{ row.phone || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ gebianShijian(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="dakaiBianji(row)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建用户弹窗 -->
    <el-dialog v-model="xinjian_duik" title="新增用户" width="520px" :close-on-click-modal="false">
      <el-form :model="xinjian_biaodan" :rules="xinjian_guize" ref="xinjianRef" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="xinjian_biaodan.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="xinjian_biaodan.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="xinjian_biaodan.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="xinjian_biaodan.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="巡检员" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="xinjian_biaodan.phone" placeholder="请输入手机号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="xinjian_duik = false">取消</el-button>
        <el-button type="primary" :loading="baocun_zhong" @click="tijiaoXinjian">确认创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户弹窗 -->
    <el-dialog v-model="bianji_duik" title="编辑用户" width="520px" :close-on-click-modal="false">
      <el-form :model="bianji_biaodan" :rules="bianji_guize" ref="bianjiRef" label-width="90px">
        <el-form-item label="用户名">
          <el-input :model-value="bianji_biaodan.username" disabled />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="bianji_biaodan.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="bianji_biaodan.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="巡检员" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="bianji_biaodan.phone" placeholder="请输入手机号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bianji_duik = false">取消</el-button>
        <el-button type="primary" :loading="baocun_zhong" @click="tijiaoBianji">确认保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Edit } from '@element-plus/icons-vue'
import { huoquYonghuLiebiao, xinzengYonghu, bianjiYonghu } from '../api'

// 筛选条件
const shaixuan_tiaojian = reactive({
  guanjianci: '',
})

// 数据列表和加载状态
const yonghu_liebiao = ref([])
const jiazai_zhong = ref(false)

// 新建弹窗
const xinjian_duik = ref(false)
const xinjianRef = ref(null)
const baocun_zhong = ref(false)

const xinjian_biaodan = reactive({
  username: '',
  password: '',
  real_name: '',
  role: 'user',
  phone: '',
})

const xinjian_guize = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

// 编辑弹窗
const bianji_duik = ref(false)
const bianjiRef = ref(null)

const bianji_biaodan = reactive({
  id: null,
  username: '',
  real_name: '',
  role: '',
  phone: '',
})

const bianji_guize = {
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

// 前端过滤列表
const guolv_liebiao = computed(() => {
  if (!shaixuan_tiaojian.guanjianci) return yonghu_liebiao.value
  const ci = shaixuan_tiaojian.guanjianci.toLowerCase()
  return yonghu_liebiao.value.filter((item) => {
    const ming = (item.username || '').toLowerCase()
    const xingming = (item.real_name || '').toLowerCase()
    return ming.includes(ci) || xingming.includes(ci)
  })
})

// 角色文字
function jueseWenzi(juese) {
  const map = { user: '巡检员', admin: '管理员', drone: '巡检员', operator: '管理员', attendant: '值守员' }
  return map[juese] || juese || '-'
}

// 角色标签类型
function jueseLeixing(juese) {
  if (juese === 'admin' || juese === 'operator') return 'danger'
  if (juese === 'user' || juese === 'drone') return 'primary'
  return 'warning'
}

// 格式化时间
function gebianShijian(shijian_zhi) {
  if (!shijian_zhi) return '-'
  const d = new Date(shijian_zhi)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 查询数据
async function chaxunShuju() {
  jiazai_zhong.value = true
  try {
    const jieguo = await huoquYonghuLiebiao()
    yonghu_liebiao.value = jieguo.users || jieguo || []
  } catch (cuowu) {
    console.error('查询用户列表失败', cuowu)
  } finally {
    jiazai_zhong.value = false
  }
}

// 打开新建弹窗
function dakaiXinjian() {
  xinjian_biaodan.username = ''
  xinjian_biaodan.password = ''
  xinjian_biaodan.real_name = ''
  xinjian_biaodan.role = 'user'
  xinjian_biaodan.phone = ''
  xinjian_duik.value = true
}

// 提交新建
async function tijiaoXinjian() {
  if (!xinjianRef.value) return
  try {
    await xinjianRef.value.validate()
    baocun_zhong.value = true
    await xinzengYonghu({ ...xinjian_biaodan })
    ElMessage.success('用户创建成功')
    xinjian_duik.value = false
    chaxunShuju()
  } catch (cuowu) {
    if (cuowu.message) ElMessage.error(cuowu.message)
  } finally {
    baocun_zhong.value = false
  }
}

// 打开编辑弹窗
function dakaiBianji(row) {
  bianji_biaodan.id = row.id
  bianji_biaodan.username = row.username
  bianji_biaodan.real_name = row.real_name || ''
  bianji_biaodan.role = row.role === 'drone' ? 'user' : row.role === 'operator' ? 'admin' : row.role
  bianji_biaodan.phone = row.phone || ''
  bianji_duik.value = true
}

// 提交编辑
async function tijiaoBianji() {
  if (!bianjiRef.value) return
  try {
    await bianjiRef.value.validate()
    baocun_zhong.value = true
    await bianjiYonghu(bianji_biaodan.id, {
      real_name: bianji_biaodan.real_name,
      role: bianji_biaodan.role,
      phone: bianji_biaodan.phone,
    })
    ElMessage.success('用户更新成功')
    bianji_duik.value = false
    chaxunShuju()
  } catch (cuowu) {
    if (cuowu.message) ElMessage.error(cuowu.message)
  } finally {
    baocun_zhong.value = false
  }
}

onMounted(() => {
  chaxunShuju()
})
</script>

<style scoped>
.yonghu_yemian {
  width: 100%;
}

.caozuo_lan {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
