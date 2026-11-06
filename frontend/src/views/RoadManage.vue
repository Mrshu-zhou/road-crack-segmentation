<template>
  <div class="daolu_yemian">
    <el-card shadow="hover">
      <!-- 顶部操作栏 -->
      <div class="caozuo_lan">
        <el-form :inline="true" :model="shaixuan_tiaojian">
          <el-form-item label="道路搜索">
            <el-input
              v-model="shaixuan_tiaojian.guanjianci"
              placeholder="输入道路名称搜索"
              clearable
              style="width: 220px"
              @keyup.enter="chaxunShuju"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="chaxunShuju">查询</el-button>
            <el-button :icon="Refresh" @click="chongzhiShaixuan">重置</el-button>
          </el-form-item>
        </el-form>
        <el-button type="primary" :icon="Plus" @click="dakaiXinjian">新增道路</el-button>
      </div>

      <!-- 数据表格 -->
      <el-table :data="guolv_liebiao" v-loading="jiazai_zhong" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column label="道路名称" min-width="140">
          <template #default="{ row }">
            {{ row.road_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="路段/区域" min-width="120">
          <template #default="{ row }">
            {{ row.section || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="道路类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.road_type || '普通道路' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="经度" width="120" align="center">
          <template #default="{ row }">
            {{ row.longitude ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="纬度" width="120" align="center">
          <template #default="{ row }">
            {{ row.latitude ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="巡检员" width="120" align="center">
          <template #default="{ row }">
            {{ row.inspector_name || row.inspector_id || '未分配' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="dakaiBianji(row)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button type="danger" link @click="querenShanchu(row)">
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="bianji_duik"
      :title="bianji_moshi === 'xinjian' ? '新增道路' : '编辑道路'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form :model="biaodan_shuju" :rules="biaodan_guize" ref="biaodanRef" label-width="90px">
        <el-form-item label="道路名称" prop="road_name">
          <el-input v-model="biaodan_shuju.road_name" placeholder="请输入道路名称" />
        </el-form-item>
        <el-form-item label="路段区域" prop="section">
          <el-input v-model="biaodan_shuju.section" placeholder="请输入路段/区域" />
        </el-form-item>
        <el-form-item label="道路类型" prop="road_type">
          <el-select v-model="biaodan_shuju.road_type" placeholder="请选择道路类型" style="width: 100%">
            <el-option label="高速公路" value="高速公路" />
            <el-option label="主干道" value="主干道" />
            <el-option label="次干道" value="次干道" />
            <el-option label="城市主干道" value="城市主干道" />
            <el-option label="城市次干道" value="城市次干道" />
            <el-option label="乡村公路" value="乡村公路" />
            <el-option label="桥梁" value="桥梁" />
            <el-option label="隧道" value="隧道" />
          </el-select>
        </el-form-item>
        <el-form-item label="经度" prop="longitude">
          <el-input-number v-model="biaodan_shuju.longitude" :precision="6" :step="0.0001" :controls="false" style="width: 100%" placeholder="经度" />
        </el-form-item>
        <el-form-item label="纬度" prop="latitude">
          <el-input-number v-model="biaodan_shuju.latitude" :precision="6" :step="0.0001" :controls="false" style="width: 100%" placeholder="纬度" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bianji_duik = false">取消</el-button>
        <el-button type="primary" :loading="baocun_zhong" @click="tijiaoBiaodan">确认保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { huoquDaoluLiebiao, xinzengDaolu, bianjiDaolu, shanchuDaolu } from '../api'

// 筛选条件
const shaixuan_tiaojian = reactive({
  guanjianci: '',
})

// 数据列表和加载状态
const daolu_liebiao = ref([])
const jiazai_zhong = ref(false)

// 弹窗相关
const bianji_duik = ref(false)
const bianji_moshi = ref('xinjian') // xinjian 或 bianji
const biaodanRef = ref(null)
const baocun_zhong = ref(false)

// 表单数据
const biaodan_shuju = reactive({
  id: null,
  road_name: '',
  section: '',
  road_type: '',
  longitude: null,
  latitude: null,
})

// 表单校验规则
const biaodan_guize = {
  road_name: [{ required: true, message: '请输入道路名称', trigger: 'blur' }],
  section: [{ required: true, message: '请输入路段区域', trigger: 'blur' }],
}

// 前端过滤后的列表
const guolv_liebiao = computed(() => {
  if (!shaixuan_tiaojian.guanjianci) return daolu_liebiao.value
  const ci = shaixuan_tiaojian.guanjianci.toLowerCase()
  return daolu_liebiao.value.filter((item) => {
    const ming = (item.road_name || '').toLowerCase()
    const qu = (item.section || '').toLowerCase()
    return ming.includes(ci) || qu.includes(ci)
  })
})

// 查询数据
async function chaxunShuju() {
  jiazai_zhong.value = true
  try {
    const jieguo = await huoquDaoluLiebiao()
    // 兼容返回格式
    if (Array.isArray(jieguo)) {
      daolu_liebiao.value = jieguo
    } else if (jieguo.roads) {
      daolu_liebiao.value = jieguo.roads
    } else if (jieguo.sites) {
      // 展开分组数据
      const zhankai = []
      jieguo.sites.forEach((quyu) => {
        if (quyu.children) {
          quyu.children.forEach((dianwei) => {
            zhankai.push({ ...dianwei, area: quyu.area })
          })
        }
      })
      daolu_liebiao.value = zhankai
    } else {
      daolu_liebiao.value = []
    }
  } catch (cuowu) {
    console.error('查询道路列表失败', cuowu)
  } finally {
    jiazai_zhong.value = false
  }
}

// 重置筛选
function chongzhiShaixuan() {
  shaixuan_tiaojian.guanjianci = ''
}

// 打开新建弹窗
function dakaiXinjian() {
  bianji_moshi.value = 'xinjian'
  biaodan_shuju.id = null
  biaodan_shuju.road_name = ''
  biaodan_shuju.section = ''
  biaodan_shuju.road_type = ''
  biaodan_shuju.longitude = null
  biaodan_shuju.latitude = null
  bianji_duik.value = true
}

// 打开编辑弹窗
function dakaiBianji(row) {
  bianji_moshi.value = 'bianji'
  biaodan_shuju.id = row.id
  biaodan_shuju.road_name = row.road_name || ''
  biaodan_shuju.section = row.section || ''
  biaodan_shuju.road_type = row.road_type || ''
  biaodan_shuju.longitude = row.longitude ?? null
  biaodan_shuju.latitude = row.latitude ?? null
  bianji_duik.value = true
}

// 提交表单
async function tijiaoBiaodan() {
  if (!biaodanRef.value) return
  try {
    await biaodanRef.value.validate()
    baocun_zhong.value = true
    const shuju = {
      road_name: biaodan_shuju.road_name,
      section: biaodan_shuju.section,
      road_type: biaodan_shuju.road_type,
      longitude: biaodan_shuju.longitude,
      latitude: biaodan_shuju.latitude,
    }
    if (bianji_moshi.value === 'xinjian') {
      await xinzengDaolu(shuju)
      ElMessage.success('道路新增成功')
    } else {
      await bianjiDaolu(biaodan_shuju.id, shuju)
      ElMessage.success('道路更新成功')
    }
    bianji_duik.value = false
    chaxunShuju()
  } catch (cuowu) {
    if (cuowu.message) ElMessage.error(cuowu.message)
  } finally {
    baocun_zhong.value = false
  }
}

// 确认删除
async function querenShanchu(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除道路 "${row.road_name}" 吗？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' },
    )
    await shanchuDaolu(row.id)
    ElMessage.success('删除成功')
    chaxunShuju()
  } catch (cuowu) {
    if (cuowu !== 'cancel' && cuowu.message) {
      ElMessage.error(cuowu.message)
    }
  }
}

onMounted(() => {
  chaxunShuju()
})
</script>

<style scoped>
.daolu_yemian {
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
