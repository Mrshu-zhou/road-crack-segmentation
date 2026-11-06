<template>
  <div class="gongdan_yemian">
    <el-card shadow="hover">
      <!-- 筛选栏 -->
      <div class="shaixuan_lan">
        <el-form :inline="true" :model="shaixuan_tiaojian">
          <el-form-item label="工单状态">
            <el-select
              v-model="shaixuan_tiaojian.status"
              placeholder="全部状态"
              clearable
              style="width: 160px"
            >
              <el-option label="待处理" value="pending" />
              <el-option label="处理中" value="processing" />
              <el-option label="已完成" value="completed" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="chaxunShuju">查询</el-button>
            <el-button :icon="Refresh" @click="chongzhiShaixuan">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 数据表格 -->
      <el-table :data="gongdan_liebiao" v-loading="jiazai_zhong" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column label="道路名称" min-width="130">
          <template #default="{ row }">
            {{ row.road_name || '未知' }}
          </template>
        </el-table-column>
        <el-table-column prop="queshi_leixing" label="缺陷类型" min-width="110" />
        <el-table-column prop="yansong_chengdu" label="严重程度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="yanzchengLeixing(row.yansong_chengdu)" effect="dark" size="small">
              {{ row.yansong_chengdu || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="修复建议" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.chuli_jianyi || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="zhuangtaiLeixing(row.status)" size="small">
              {{ zhuangtaiWenzi(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            {{ gebianShijian(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click="dakaiChuli(row)"
              :disabled="row.status === 'completed'"
            >
              <el-icon><Edit /></el-icon>
              处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="fenye_qu">
        <el-pagination
          v-model:current-page="fenye.dangqian_ye"
          v-model:page-size="fenye.ye_daxiao"
          :total="fenye.zongshu"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="chaxunShuju"
          @current-change="chaxunShuju"
        />
      </div>
    </el-card>

    <!-- 处理工单弹窗 -->
    <el-dialog v-model="chuli_duik" title="处理工单" width="500px" :close-on-click-modal="false">
      <el-form :model="chuli_biaodan" label-width="90px">
        <el-form-item label="工单ID">
          <span>{{ dangqian_gongdan?.id }}</span>
        </el-form-item>
        <el-form-item label="缺陷类型">
          <span>{{ dangqian_gongdan?.queshi_leixing || '-' }}</span>
        </el-form-item>
        <el-form-item label="严重程度">
          <el-tag :type="yanzchengLeixing(dangqian_gongdan?.yansong_chengdu)" effect="dark" size="small">
            {{ dangqian_gongdan?.yansong_chengdu || '-' }}
          </el-tag>
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select v-model="chuli_biaodan.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理结果">
          <el-input
            v-model="chuli_biaodan.result_note"
            type="textarea"
            :rows="4"
            placeholder="请填写处理结果说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="chuli_duik = false">取消</el-button>
        <el-button type="primary" :loading="baocun_zhong" @click="tijiaoChuli">确认处理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Edit } from '@element-plus/icons-vue'
import { huoquGongdanLiebiao, gengxinGongdan } from '../api'

// 筛选条件
const shaixuan_tiaojian = reactive({
  status: '',
})

// 分页配置
const fenye = reactive({
  dangqian_ye: 1,
  ye_daxiao: 10,
  zongshu: 0,
})

// 数据列表和加载状态
const gongdan_liebiao = ref([])
const jiazai_zhong = ref(false)

// 处理弹窗相关
const chuli_duik = ref(false)
const dangqian_gongdan = ref(null)
const chuli_biaodan = reactive({
  status: '',
  result_note: '',
})
const baocun_zhong = ref(false)

// 严重程度标签类型
function yanzchengLeixing(zhi) {
  if (zhi === '严重') return 'danger'
  if (zhi === '中等') return 'warning'
  if (zhi === '轻微') return 'success'
  return 'info'
}

// 工单状态文字
function zhuangtaiWenzi(zhuangtai) {
  const map = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
  }
  return map[zhuangtai] || zhuangtai || '-'
}

// 工单状态标签类型
function zhuangtaiLeixing(zhuangtai) {
  const map = {
    pending: 'danger',
    processing: 'warning',
    completed: 'success',
  }
  return map[zhuangtai] || 'info'
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
    const canshu = {
      page: fenye.dangqian_ye,
      page_size: fenye.ye_daxiao,
    }
    if (shaixuan_tiaojian.status) canshu.status = shaixuan_tiaojian.status

    const jieguo = await huoquGongdanLiebiao(canshu)
    gongdan_liebiao.value = jieguo.items || []
    fenye.zongshu = jieguo.total || 0
  } catch (cuowu) {
    console.error('查询工单列表失败', cuowu)
  } finally {
    jiazai_zhong.value = false
  }
}

// 重置筛选
function chongzhiShaixuan() {
  shaixuan_tiaojian.status = ''
  fenye.dangqian_ye = 1
  chaxunShuju()
}

// 打开处理弹窗
function dakaiChuli(gongdan) {
  dangqian_gongdan.value = gongdan
  chuli_biaodan.status = gongdan.status === 'pending' ? 'processing' : gongdan.status
  chuli_biaodan.result_note = gongdan.result_note || ''
  chuli_duik.value = true
}

// 提交处理
async function tijiaoChuli() {
  if (!chuli_biaodan.status) {
    ElMessage.warning('请选择处理状态')
    return
  }
  baocun_zhong.value = true
  try {
    await gengxinGongdan(dangqian_gongdan.value.id, {
      status: chuli_biaodan.status,
      result_note: chuli_biaodan.result_note,
    })
    ElMessage.success('工单处理成功')
    chuli_duik.value = false
    chaxunShuju()
  } catch (cuowu) {
    ElMessage.error(cuowu.message || '处理失败')
  } finally {
    baocun_zhong.value = false
  }
}

onMounted(() => {
  chaxunShuju()
})
</script>

<style scoped>
.gongdan_yemian {
  width: 100%;
}

.shaixuan_lan {
  margin-bottom: 16px;
}

.fenye_qu {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
