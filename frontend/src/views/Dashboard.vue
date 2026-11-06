<template>
  <div class="yibiaopan_yemian">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="tongji_xing">
      <el-col :xs="12" :sm="6">
        <div class="tongji_kapian kapian_lan">
          <div class="tongji_tubiao">
            <el-icon><Search /></el-icon>
          </div>
          <div class="tongji_shuju">
            <div class="shuju_shuzi">{{ tongji.xunjian_zongshu }}</div>
            <div class="shuju_biaoti">巡检总数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="tongji_kapian kapian_cheng">
          <div class="tongji_tubiao">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <div class="tongji_shuju">
            <div class="shuju_shuzi">{{ tongji.quexian_shu }}</div>
            <div class="shuju_biaoti">缺陷数量</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="tongji_kapian kapian_hong">
          <div class="tongji_tubiao">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="tongji_shuju">
            <div class="shuju_shuzi">{{ tongji.daichuli_gongdan }}</div>
            <div class="shuju_biaoti">待处理工单</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="tongji_kapian kapian_lv">
          <div class="tongji_tubiao">
            <el-icon><CircleCheckFilled /></el-icon>
          </div>
          <div class="tongji_shuju">
            <div class="shuju_shuzi">{{ tongji.yiwancheng_gongdan }}</div>
            <div class="shuju_biaoti">已完成工单</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="tubiao_xing">
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="tubiao_kapian">
          <template #header>
            <div class="kapian_tou">
              <el-icon><PieChart /></el-icon>
              <span>缺陷类型分布</span>
            </div>
          </template>
          <div ref="quexianBingtu" class="tubiao_rongqi"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="tubiao_kapian">
          <template #header>
            <div class="kapian_tou">
              <el-icon><Histogram /></el-icon>
              <span>严重程度分布</span>
            </div>
          </template>
          <div ref="yanchengZhutu" class="tubiao_rongqi"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="tubiao_kapian">
          <template #header>
            <div class="kapian_tou">
              <el-icon><DataLine /></el-icon>
              <span>工单状态统计</span>
            </div>
          </template>
          <div ref="gongdanZhuangtai" class="tubiao_rongqi"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近巡检记录 -->
    <el-card shadow="hover" class="zuijin_kapian">
      <template #header>
        <div class="kapian_tou">
          <el-icon><List /></el-icon>
          <span>最近巡检记录</span>
          <el-button type="primary" link class="chakan_quanbu" @click="$router.push('/inspections')">
            查看全部
          </el-button>
        </div>
      </template>
      <el-table :data="zuijin_xunjian" v-loading="jiazai_zhong" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="缩略图" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.image_url"
              :src="tupianDizhi(row.image_url)"
              fit="cover"
              class="suolvetu"
              :preview-src-list="[tupianDizhi(row.image_url)]"
              preview-teleported
            />
            <span v-else class="wu_tu_wenzi">无图片</span>
          </template>
        </el-table-column>
        <el-table-column label="道路名称" min-width="150">
          <template #default="{ row }">
            {{ row.road_name || '未知道路' }}
          </template>
        </el-table-column>
        <el-table-column label="缺陷类型" min-width="100">
          <template #default="{ row }">
            {{ row.ai_result?.queshi_leixing || '无' }}
          </template>
        </el-table-column>
        <el-table-column label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="yanzchengLeixing(row.ai_result?.yansong_chengdu)" effect="dark" size="small">
              {{ row.ai_result?.yansong_chengdu || '无' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            {{ gebianShijian(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="$router.push(`/inspections/${row.id}`)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { huoquYibiaopan, huoquXunjianLiebiao } from '../api'

// 统计数据
const tongji = reactive({
  xunjian_zongshu: 0,
  quexian_shu: 0,
  daichuli_gongdan: 0,
  yiwancheng_gongdan: 0,
})

// 最近巡检记录
const zuijin_xunjian = ref([])
// 加载状态
const jiazai_zhong = ref(false)

// 图表引用
const quexianBingtu = ref(null)
const yanchengZhutu = ref(null)
const gongdanZhuangtai = ref(null)

// 图表实例
let bingtu_shili = null
let zhutu_shili = null
let zhuangtai_shili = null

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

// 严重程度对应的标签类型
function yanzchengLeixing(zhi) {
  if (zhi === '严重') return 'danger'
  if (zhi === '中等') return 'warning'
  if (zhi === '轻微') return 'success'
  return 'info'
}

// 加载仪表盘数据
async function jiazaiShuju() {
  jiazai_zhong.value = true
  try {
    const zonglan = await huoquYibiaopan()

    // 统计卡片数据
    tongji.xunjian_zongshu = zonglan.total_inspections || 0
    tongji.daichuli_gongdan = zonglan.pending_workorders || 0
    tongji.yiwancheng_gongdan = zonglan.completed_workorders || 0

    // 计算缺陷数量：总数减去无缺陷的
    const quexian_fenbu = zonglan.defect_type_distribution || {}
    const wu_quexian = (quexian_fenbu['无'] || 0) + (quexian_fenbu['无法识别'] || 0)
    tongji.quexian_shu = tongji.xunjian_zongshu - wu_quexian

    // 获取最近5条巡检
    const xunjian = await huoquXunjianLiebiao({ page: 1, page_size: 5 })
    zuijin_xunjian.value = xunjian.items || []

    // 绘制图表
    await nextTick()
    huiZhiTubiao(zonglan)
  } catch (cuowu) {
    console.error('加载仪表盘数据失败', cuowu)
  } finally {
    jiazai_zhong.value = false
  }
}

// 绘制所有图表
function huiZhiTubiao(zonglan) {
  huiZhiQuexianBingtu(zonglan)
  huiZhiYanchengZhutu(zonglan)
  huiZhiGongdanZhuangtai(zonglan)
}

// 缺陷类型分布饼图（使用后端统计的全量数据）
function huiZhiQuexianBingtu(zonglan) {
  if (!quexianBingtu.value) return
  bingtu_shili = echarts.init(quexianBingtu.value)

  const fenbu = zonglan.defect_type_distribution || {}
  const shuju = Object.entries(fenbu).map(([mingcheng, shuzhi]) => ({
    name: mingcheng,
    value: shuzhi,
  }))

  bingtu_shili.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: '5%', left: 'center' },
    color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#9c27b0', '#00bcd4'],
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data: shuju.length ? shuju : [{ name: '暂无数据', value: 1 }],
      },
    ],
  })
}

// 严重程度分布柱状图（使用后端统计的全量数据）
function huiZhiYanchengZhutu(zonglan) {
  if (!yanchengZhutu.value) return
  zhutu_shili = echarts.init(yanchengZhutu.value)

  const fenbu = zonglan.severity_distribution || {}
  const leixing_shunxu = ['轻微', '中等', '严重', '无']
  const yanse = ['#67c23a', '#e6a23c', '#f56c6c', '#909399']

  zhutu_shili.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '10%', right: '10%', bottom: '15%', top: '10%' },
    xAxis: {
      type: 'category',
      data: leixing_shunxu,
      axisLabel: { fontSize: 12 },
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        type: 'bar',
        data: leixing_shunxu.map((lx, i) => ({
          value: fenbu[lx] || 0,
          itemStyle: { color: yanse[i] },
        })),
        barWidth: '40%',
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: 'top' },
      },
    ],
  })
}

// 工单状态统计饼图
function huiZhiGongdanZhuangtai(zonglan) {
  if (!gongdanZhuangtai.value) return
  zhuangtai_shili = echarts.init(gongdanZhuangtai.value)

  const shuju = [
    { name: '待处理', value: zonglan.pending_workorders || 0, itemStyle: { color: '#f56c6c' } },
    { name: '处理中', value: zonglan.processing_workorders || 0, itemStyle: { color: '#e6a23c' } },
    { name: '已完成', value: zonglan.completed_workorders || 0, itemStyle: { color: '#67c23a' } },
  ]

  zhuangtai_shili.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: '5%', left: 'center' },
    series: [
      {
        type: 'pie',
        radius: '60%',
        center: ['50%', '45%'],
        data: shuju,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b}\n{c}' },
      },
    ],
  })
}

// 窗口大小变化时重绘图表
function chuangkouBianhua() {
  bingtu_shili?.resize()
  zhutu_shili?.resize()
  zhuangtai_shili?.resize()
}

onMounted(() => {
  jiazaiShuju()
  window.addEventListener('resize', chuangkouBianhua)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', chuangkouBianhua)
  bingtu_shili?.dispose()
  zhutu_shili?.dispose()
  zhuangtai_shili?.dispose()
})
</script>

<style scoped>
.yibiaopan_yemian {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 统计卡片行 */
.tongji_xing {
  margin-bottom: 0;
}

.tongji_kapian {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 10px;
  color: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.tongji_kapian:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.kapian_lan {
  background: linear-gradient(135deg, #409eff 0%, #1d6fd1 100%);
}

.kapian_cheng {
  background: linear-gradient(135deg, #e6a23c 0%, #cf8a2e 100%);
}

.kapian_hong {
  background: linear-gradient(135deg, #f56c6c 0%, #d94f4f 100%);
}

.kapian_lv {
  background: linear-gradient(135deg, #67c23a 0%, #4e9e2a 100%);
}

.tongji_tubiao {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.shuju_shuzi {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.shuju_biaoti {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

/* 图表卡片 */
.tubiao_kapian {
  margin-bottom: 20px;
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

.chakan_quanbu {
  margin-left: auto;
}

.tubiao_rongqi {
  height: 300px;
  width: 100%;
}

/* 最近巡检卡片 */
.zuijin_kapian .suolvetu {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  cursor: pointer;
}

.wu_tu_wenzi {
  font-size: 12px;
  color: #c0c4cc;
}
</style>
