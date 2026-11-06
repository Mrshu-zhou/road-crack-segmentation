<template>
  <div class="xiangqing_yemian" v-loading="jiazai_zhong">
    <!-- 顶部返回按钮 -->
    <div class="fanhui_lan">
      <el-button :icon="ArrowLeft" @click="$router.back()">返回列表</el-button>
    </div>

    <el-row :gutter="20" v-if="xunjian_shuju">
      <!-- 左侧：巡检图片展示 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="tupian_kapian">
          <template #header>
            <div class="kapian_tou">
              <el-icon><Picture /></el-icon>
              <span>巡检图片</span>
            </div>
          </template>
          <div class="datu_rongqi">
            <el-image
              v-if="xunjian_shuju.image_url"
              :src="tupianDizhi(xunjian_shuju.image_url)"
              fit="contain"
              class="xunjian_datu"
              :preview-src-list="yulan_tupian_liebiao"
              preview-teleported
            />
            <el-empty v-else description="暂无图片" />
          </div>

          <!-- 基本信息展示 -->
          <el-descriptions :column="2" border class="jiben_xinxi">
            <el-descriptions-item label="巡检ID">{{ xunjian_shuju.id }}</el-descriptions-item>
            <el-descriptions-item label="巡检状态">
              <el-tag type="success" size="small">{{ zhuangtaiWenzi(xunjian_shuju.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="道路名称">{{ xunjian_shuju.road_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="路段">{{ xunjian_shuju.section || '-' }}</el-descriptions-item>
            <el-descriptions-item label="巡检员">{{ xunjian_shuju.inspector_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="巡检时间">{{ gebianShijian(xunjian_shuju.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 右侧：AI 分析结果 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="kapian_tou">
              <el-icon><Cpu /></el-icon>
              <span>AI 智能分析结果</span>
            </div>
          </template>
          <AiResultCard :ai-result="xunjian_shuju.ai_result || {}" :image-url="xunjian_shuju.image_url ? tupianDizhi(xunjian_shuju.image_url) : ''" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 裂缝分割结果 -->
    <el-card v-if="fenge_jieguo" shadow="hover" class="fenge_kapian">
      <template #header>
        <div class="kapian_tou">
          <el-icon><Aim /></el-icon>
          <span>裂缝像素级分割结果</span>
        </div>
      </template>

      <el-row :gutter="16">
        <el-col :xs="24" :sm="12">
          <div class="fenge_biaoti">缺陷叠加图</div>
          <el-image
            :src="tupianDizhi(fenge_jieguo.overlay_url)"
            fit="contain"
            class="fenge_tu"
            :preview-src-list="[tupianDizhi(fenge_jieguo.overlay_url), tupianDizhi(fenge_jieguo.mask_url)]"
            preview-teleported
          />
        </el-col>
        <el-col :xs="24" :sm="12">
          <div class="fenge_biaoti">分割掩码</div>
          <el-image
            :src="tupianDizhi(fenge_jieguo.mask_url)"
            fit="contain"
            class="fenge_tu"
            :preview-src-list="[tupianDizhi(fenge_jieguo.mask_url), tupianDizhi(fenge_jieguo.overlay_url)]"
            preview-teleported
          />
        </el-col>
      </el-row>

      <el-descriptions :column="3" border size="small" class="fenge_miaoshu">
        <el-descriptions-item label="模型">
          {{ xunjian_shuju.ai_result?.model_label || fenge_jieguo.model_key || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="预处理">
          {{ fenge_jieguo.preprocess_mode || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="推理耗时">
          {{ fenge_jieguo.latency_ms }} ms
        </el-descriptions-item>
        <el-descriptions-item label="裂缝处数">
          {{ fenge_jieguo.quantification?.defect_count ?? '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="累计长度">
          {{ geShi(fenge_jieguo.quantification?.length_mm) }} mm
        </el-descriptions-item>
        <el-descriptions-item label="最大宽度">
          {{ geShi(fenge_jieguo.quantification?.width_max_mm) }} mm
        </el-descriptions-item>
        <el-descriptions-item label="面积占比">
          {{ geShi((fenge_jieguo.quantification?.area_ratio || 0) * 100, 2) }}%
        </el-descriptions-item>
        <el-descriptions-item label="严重程度" :span="2">
          <el-tag :type="yanzchengLeixing(fenge_jieguo.quantification?.grade)" effect="dark" size="small">
            {{ fenge_jieguo.quantification?.grade || '-' }}
          </el-tag>
          <span class="fenge_yiju">{{ fenge_jieguo.quantification?.grade_reason || '' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 底部：关联工单信息 -->
    <el-card v-if="xunjian_shuju && xunjian_shuju.workorders && xunjian_shuju.workorders.length" shadow="hover" class="gongdan_kapian">
      <template #header>
        <div class="kapian_tou">
          <el-icon><Tickets /></el-icon>
          <span>关联工单信息</span>
        </div>
      </template>
      <el-table :data="xunjian_shuju.workorders" border stripe>
        <el-table-column prop="id" label="工单ID" width="80" align="center" />
        <el-table-column prop="queshi_leixing" label="缺陷类型" min-width="120" />
        <el-table-column prop="yansong_chengdu" label="严重程度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="yanzchengLeixing(row.yansong_chengdu)" effect="dark" size="small">
              {{ row.yansong_chengdu || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chuli_jianyi" label="修复建议" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="工单状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="gongdanZhuangtaiLeixing(row.status)" size="small">
              {{ gongdanZhuangtaiWenzi(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            {{ gebianShijian(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { huoquXunjianXiangqing } from '../api'
import AiResultCard from '../components/AiResultCard.vue'

const route = useRoute()

// 巡检数据
const xunjian_shuju = ref(null)
const jiazai_zhong = ref(false)

// 分割结果（AI 结果中的 seg 字段）
const fenge_jieguo = computed(() => xunjian_shuju.value?.ai_result?.seg || null)

function geShi(shuzhi, weishu = 1) {
  if (shuzhi === null || shuzhi === undefined || Number.isNaN(Number(shuzhi))) return '-'
  return Number(shuzhi).toFixed(weishu)
}

// 预览图片列表
const yulan_tupian_liebiao = computed(() => {
  if (!xunjian_shuju.value) return []
  if (xunjian_shuju.value.image_url) {
    return [tupianDizhi(xunjian_shuju.value.image_url)]
  }
  return []
})

// 图片地址处理
function tupianDizhi(lujing) {
  if (!lujing) return ''
  if (lujing.startsWith('http')) return lujing
  return lujing.replace(/^.*uploads/, '/uploads')
}

// 格式化时间
function gebianShijian(shijian_zhi) {
  if (!shijian_zhi) return '-'
  const d = new Date(shijian_zhi)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 状态文字
function zhuangtaiWenzi(zhuangtai) {
  const map = { completed: '已完成', pending: '待处理', processing: '处理中' }
  return map[zhuangtai] || zhuangtai || '已完成'
}

// 严重程度标签类型
function yanzchengLeixing(zhi) {
  if (zhi === '严重') return 'danger'
  if (zhi === '中等') return 'warning'
  if (zhi === '轻微') return 'success'
  return 'info'
}

// 工单状态文字
function gongdanZhuangtaiWenzi(zhuangtai) {
  const map = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
  }
  return map[zhuangtai] || zhuangtai || '-'
}

// 工单状态标签类型
function gongdanZhuangtaiLeixing(zhuangtai) {
  const map = {
    pending: 'danger',
    processing: 'warning',
    completed: 'success',
  }
  return map[zhuangtai] || 'info'
}

// 加载巡检详情
async function jiazaiXiangqing() {
  const id = route.params.id
  if (!id) return

  jiazai_zhong.value = true
  try {
    xunjian_shuju.value = await huoquXunjianXiangqing(id)
  } catch (cuowu) {
    console.error('加载巡检详情失败', cuowu)
  } finally {
    jiazai_zhong.value = false
  }
}

onMounted(() => {
  jiazaiXiangqing()
})
</script>

<style scoped>
.xiangqing_yemian {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.fanhui_lan {
  margin-bottom: 0;
}

.kapian_tou {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}

.kapian_tou .el-icon {
  color: #409eff;
  font-size: 18px;
}

.tupian_kapian {
  margin-bottom: 20px;
}

.datu_rongqi {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  max-height: 500px;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

.xunjian_datu {
  max-width: 100%;
  max-height: 500px;
  cursor: pointer;
}

.jiben_xinxi {
  margin-top: 16px;
}

.gongdan_kapian {
  margin-top: 0;
}

.fenge_kapian {
  margin-top: 0;
}

.fenge_biaoti {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 6px;
}

.fenge_tu {
  width: 100%;
  height: 260px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: zoom-in;
}

.fenge_miaoshu {
  margin-top: 14px;
}

.fenge_yiju {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}
</style>
