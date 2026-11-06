<template>
  <div class="liebiao_yemian">
    <el-card shadow="hover">
      <!-- 筛选栏 -->
      <div class="shaixuan_lan">
        <el-form :inline="true" :model="shaixuan_tiaojian">
          <el-form-item label="缺陷类型">
            <el-select
              v-model="shaixuan_tiaojian.defect_type"
              placeholder="全部"
              clearable
              style="width: 160px"
            >
              <el-option
                v-for="leixing in quexian_leixing"
                :key="leixing"
                :label="leixing"
                :value="leixing"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="严重程度">
            <el-select
              v-model="shaixuan_tiaojian.severity"
              placeholder="全部"
              clearable
              style="width: 140px"
            >
              <el-option label="严重" value="严重" />
              <el-option label="中等" value="中等" />
              <el-option label="轻微" value="轻微" />
              <el-option label="无" value="无" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="chaxunShuju">查询</el-button>
            <el-button :icon="Refresh" @click="chongzhiShaixuan">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 数据表格 -->
      <el-table
        :data="xunjian_liebiao"
        v-loading="jiazai_zhong"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column label="缩略图" width="90" align="center">
          <template #default="{ row }">
            <el-image
              v-if="row.image_url"
              :src="tupianDizhi(row.image_url)"
              fit="cover"
              class="suolvetu"
              :preview-src-list="[tupianDizhi(row.image_url)]"
              preview-teleported
            />
            <el-icon v-else class="wu_tupian"><Picture /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="道路名称" min-width="160">
          <template #default="{ row }">
            <div>{{ row.road_name || '未知道路' }}</div>
            <div class="luduan_xinxi">{{ row.section || '' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="缺陷类型" min-width="120">
          <template #default="{ row }">
            {{ huoquZiduan(row, 'queshi_leixing') || '无' }}
          </template>
        </el-table-column>
        <el-table-column label="严重程度" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="yanzchengLeixing(huoquZiduan(row, 'yansong_chengdu'))"
              effect="dark"
              size="small"
            >
              {{ huoquZiduan(row, 'yansong_chengdu') || '无' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="紧急程度" width="110" align="center">
          <template #default="{ row }">
            <el-tag
              :type="jinchengLeixing(huoquZiduan(row, 'yingji_chengdu'))"
              effect="plain"
              size="small"
            >
              {{ huoquZiduan(row, 'yingji_chengdu') || '无' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="success" size="small">{{ zhuangtaiWenzi(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="巡检时间" width="170">
          <template #default="{ row }">
            {{ gebianShijian(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="chakanXiangqing(row.id)">
              <el-icon><View /></el-icon>
              查看详情
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Refresh } from '@element-plus/icons-vue'
import { huoquXunjianLiebiao } from '../api'

const router = useRouter()

// 缺陷类型选项
const quexian_leixing = ['坑洞', '裂缝', '龟裂', '车辙', '松散', '修补痕迹', '无']

// 筛选条件
const shaixuan_tiaojian = reactive({
  queshi_leixing: '',
  yansong_chengdu: '',
})

// 分页配置
const fenye = reactive({
  dangqian_ye: 1,
  ye_daxiao: 10,
  zongshu: 0,
})

// 数据列表和加载状态
const xunjian_liebiao = ref([])
const jiazai_zhong = ref(false)

// 图片地址处理
function tupianDizhi(lujing) {
  if (!lujing) return ''
  if (lujing.startsWith('http')) return lujing
  return lujing.replace(/^.*uploads/, '/uploads')
}

// 拼音字段名到中文字段名的映射
const zhongwen_ziduan = {
  queshi_leixing: '缺陷类型',
  yansong_chengdu: '严重程度',
  yingji_chengdu: '紧急程度',
}

// 获取 AI 结果字段（兼容拼音和中文字段名）
function huoquZiduan(row, ziduan) {
  const ai = row.ai_result || {}
  return ai[ziduan] ?? ai[zhongwen_ziduan[ziduan]] ?? ''
}

// 严重程度标签类型
function yanzchengLeixing(zhi) {
  if (zhi === '严重') return 'danger'
  if (zhi === '中等') return 'warning'
  if (zhi === '轻微') return 'success'
  return 'info'
}

// 紧急程度标签类型
function jinchengLeixing(zhi) {
  if (zhi === '立即封路') return 'danger'
  if (zhi === '建议绕行') return 'warning'
  if (zhi === '低速行驶通过') return 'success'
  return 'info'
}

// 状态文字
function zhuangtaiWenzi(zhuangtai) {
  const map = { completed: '已完成', pending: '待处理', processing: '处理中' }
  return map[zhuangtai] || zhuangtai || '已完成'
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
    if (shaixuan_tiaojian.queshi_leixing) canshu.queshi_leixing = shaixuan_tiaojian.queshi_leixing
    if (shaixuan_tiaojian.yansong_chengdu) canshu.yansong_chengdu = shaixuan_tiaojian.yansong_chengdu

    const jieguo = await huoquXunjianLiebiao(canshu)
    xunjian_liebiao.value = jieguo.items || []
    fenye.zongshu = jieguo.total || 0
  } catch (cuowu) {
    console.error('查询巡检列表失败', cuowu)
  } finally {
    jiazai_zhong.value = false
  }
}

// 重置筛选
function chongzhiShaixuan() {
  shaixuan_tiaojian.queshi_leixing = ''
  shaixuan_tiaojian.yansong_chengdu = ''
  fenye.dangqian_ye = 1
  chaxunShuju()
}

// 查看详情
function chakanXiangqing(id) {
  router.push(`/inspections/${id}`)
}

onMounted(() => {
  chaxunShuju()
})
</script>

<style scoped>
.liebiao_yemian {
  width: 100%;
}

.shaixuan_lan {
  margin-bottom: 16px;
}

.suolvetu {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  cursor: pointer;
}

.wu_tupian {
  font-size: 28px;
  color: #c0c4cc;
}

.luduan_xinxi {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.fenye_qu {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
