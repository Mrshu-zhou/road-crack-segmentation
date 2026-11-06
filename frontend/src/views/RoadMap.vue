<template>
  <div class="ditu_yemian">
    <el-card shadow="hover">
      <template #header>
        <div class="kapian_tou">
          <el-icon><MapLocation /></el-icon>
          <span>道路点位与缺陷分布地图</span>
          <el-button
            type="primary"
            link
            :icon="Refresh"
            class="shuaxin_anniu"
            @click="chongxinJiazai"
          >
            重新加载
          </el-button>
        </div>
      </template>

      <!-- 未配置高德 Key 时的引导提示 -->
      <el-empty
        v-if="!peiZhiWanZheng && !ditu_chushi_hua"
        description="尚未配置高德地图 Key"
      >
        <template #description>
          <div class="pei_zhi_tishi">
            <p>要在地图上展示道路点位，需要先申请高德开放平台 Key：</p>
            <ol class="pei_zhi_buzhou">
              <li>打开 <a href="https://lbs.amap.com/" target="_blank" rel="noopener">https://lbs.amap.com/</a> 注册并登录</li>
              <li>进入控制台，在"应用管理 / 我的应用"中创建新应用</li>
              <li>添加 Key：服务平台选择"Web端（JS API）"</li>
              <li>在应用详情中复制 Key 与安全密钥（securityJsCode）</li>
              <li>将两者填入本页面顶部 AMAP_KEY 与 AMAP_SECURITY 常量</li>
            </ol>
            <p class="tishi_wen">演示时该页需要联网访问高德服务</p>
          </div>
        </template>
      </el-empty>

      <!-- 地图容器 -->
      <div v-show="peiZhiWanZheng" ref="dituRongqi" class="ditu_rongqi" v-loading="ditu_jiazai">
        <el-empty v-if="ditu_jiazai" description="地图加载中..." />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Refresh, MapLocation } from '@element-plus/icons-vue'
import { huoquDaoluLiebiao, huoquXunjianLiebiao } from '../api'

// ============ 高德地图配置 ============
const AMAP_KEY = '663d031f29eab16cad39b41a2f520be4'        // 高德 Web 端 JS API Key
const AMAP_SECURITY = 'd4b39d0ec46fb80cfed83e44603ed36a'   // 高德安全密钥 securityJsCode
const AMAP_JS_URL = 'https://webapi.amap.com/maps'
// ==================================================

// 地图中心：大连市中山区附近
const DA_LIAN_ZHONG_XIN = [121.614, 38.917]
const CHU_SHI_LEVEL = 12

const dituRongqi = ref(null)
const ditu_jiazai = ref(false)
const ditu_chushi_hua = ref(false)

// 是否已填写 Key
const peiZhiWanZheng = computed(() => {
  return Boolean(AMAP_KEY) && Boolean(AMAP_SECURITY)
})

// 道路点位与缺陷统计
const daolu_shuju = ref([])
const quexian_tongji = ref({})

let ditu_shili = null
let biaoji_liebiao = []
let jia_zaiqu_kuan = null

// 加载道路与缺陷统计
async function jiazaiDaoluShuju() {
  const jieguo = await huoquDaoluLiebiao()
  const daolu = jieguo.roads || (Array.isArray(jieguo) ? jieguo : [])
  daolu_shuju.value = daolu

  // 聚合每个道路的缺陷数量（排除无缺陷）
  const tongji = {}
  const xunjian = await huoquXunjianLiebiao({ page: 1, page_size: 200 })
  for (const xj of xunjian.items || []) {
    if (!xj.road_id) continue
    const leixing = xj.ai_result?.queshi_leixing || ''
    if (leixing && !['无', '无法识别', 'API 错误', '解析错误'].includes(leixing)) {
      tongji[xj.road_id] = (tongji[xj.road_id] || 0) + 1
    }
  }
  quexian_tongji.value = tongji
}

// 等待高德脚本加载完成
function jiazaiGaodeScript() {
  return new Promise((resolve, reject) => {
    if (window.AMap) {
      resolve()
      return
    }
    window._AMapSecurityConfig = { securityJsCode: AMAP_SECURITY }
    const script = document.createElement('script')
    script.src = `${AMAP_JS_URL}?v=2.0&key=${AMAP_KEY}&plugin=AMap.Scale,AMap.ToolBar`
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('高德地图脚本加载失败，请检查网络与 Key'))
    document.head.appendChild(script)
  })
}

// 初始化地图与标注
async function chushiHuaDitu() {
  if (!peiZhiWanZheng.value || ditu_shili) return
  ditu_jiazai.value = true
  try {
    await jiazaiDaoluShuju()
    await jiazaiGaodeScript()

    ditu_shili = new window.AMap.Map(dituRongqi.value, {
      zoom: CHU_SHI_LEVEL,
      center: DA_LIAN_ZHONG_XIN,
      viewMode: '2D',
    })
    ditu_shili.addControl(new window.AMap.Scale())
    ditu_shili.addControl(new window.AMap.ToolBar({ position: 'RT' }))

    huiZhiBiaoji()
    ditu_chushi_hua.value = true
  } catch (cuowu) {
    console.error('地图初始化失败', cuowu)
  } finally {
    ditu_jiazai.value = false
  }
}

// 在地图上绘制道路点位标注
function huiZhiBiaoji() {
  lianJieKongXian(true)
  biaoji_liebiao.forEach((biaoji) => biaoji.setMap(null))
  biaoji_liebiao = []

  for (const daolu of daolu_shuju.value) {
    if (daolu.longitude == null || daolu.latitude == null) continue
    const quexian_shu = quexian_tongji.value[daolu.id] || 0

    const biaoji = new window.AMap.Marker({
      position: [daolu.longitude, daolu.latitude],
      title: daolu.road_name,
      content: createMarkerContent(quexian_shu),
      offset: new window.AMap.Pixel(-16, -16),
    })

    const neirong = `
      <div class="map_tanchuang">
        <div class="map_tc_biaoti">${daolu.road_name || '未知道路'}</div>
        <div class="map_tc_neirong">路段：${daolu.section || '-'}</div>
        <div class="map_tc_neirong">类型：${daolu.road_type || '-'}</div>
        <div class="map_tc_neirong map_tc_quexian">累计缺陷：${quexian_shu} 处</div>
      </div>`
    biaoji.on('click', () => {
      const xinxi = new window.AMap.InfoWindow({ content: neirong, offset: new window.AMap.Pixel(0, -30) })
      xinxi.open(ditu_shili, [daolu.longitude, daolu.latitude])
    })

    biaoji_liebiao.push(biaoji)
    ditu_shili.add(biaoji)
  }
  zuiShiFangwei()
}

// 生成本地标注点样式（无缺陷蓝色，有缺陷红色）
function createMarkerContent(quexian_shu) {
  const yanse = quexian_shu > 0 ? '#f56c6c' : '#409eff'
  return `<div class="map_dingwei_wai"><div class="map_dingwei_dian" style="background:${yanse}"></div></div>`
}

// 根据点位范围自适应视野
function zuiShiFangwei() {
  if (!biaoji_liebiao.length) return
  const jihe = new window.AMap.ArrayBounds(biaoji_liebiao.map((b) => b.getPosition()))
  ditu_shili.setFitView(jihe, false, [60, 60, 60, 60])
}

// 重置连线层（预留：后续可画航线/覆盖范围）
function lianJieKongXian(clear = false) {
  if (clear && jia_zaiqu_kuan) {
    jia_zaiqu_kuan.setMap(null)
    jia_zaiqu_kuan = null
  }
}

// 重新加载（修复数据变化后刷新标注）
async function chongxinJiazai() {
  if (ditu_shili) {
    await jiazaiDaoluShuju()
    huiZhiBiaoji()
  } else {
    await chushiHuaDitu()
  }
}

onMounted(() => {
  if (peiZhiWanZheng.value) {
    chushiHuaDitu()
  }
})

onBeforeUnmount(() => {
  ditu_shili?.destroy()
  ditu_shili = null
  biaoji_liebiao = []
})
</script>

<style scoped>
.ditu_yemian {
  width: 100%;
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

.shuaxin_anniu {
  margin-left: auto;
}

.ditu_rongqi {
  height: 620px;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
}

.pei_zhi_tishi {
  text-align: left;
  max-width: 560px;
  margin: 0 auto;
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
}

.pei_zhi_tishi a {
  color: #409eff;
}

.pei_zhi_buzhou {
  padding-left: 20px;
  margin: 8px 0;
}

.tishi_wen {
  color: #e6a23c;
  margin-top: 4px;
}

/* 地图内嵌样式（非 scoped，需全局生效） */
:global(.map_dingwei_wai) {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(.map_dingwei_dian) {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
}

:global(.map_tanchuang) {
  padding: 4px 2px;
  line-height: 1.7;
}

:global(.map_tc_biaoti) {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

:global(.map_tc_quexian) {
  color: #f56c6c;
  font-weight: 600;
}
</style>