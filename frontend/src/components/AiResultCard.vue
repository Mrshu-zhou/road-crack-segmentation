<template>
  <div class="ai_jieguo_rongqi">
    <!-- 缺陷定位画框展示 -->
    <div v-if="youDingweiTu" class="dingwei_kuai">
      <div class="dingwei_tou">
        <el-icon color="#f56c6c"><Location /></el-icon>
        <span>缺陷定位与量化</span>
        <el-tag size="small" type="danger" effect="plain">{{ qingdanYouKuang.length }} 处缺陷</el-tag>
      </div>
      <div class="tupian_dingwei">
        <img :src="imageUrl" class="dingwei_tu" alt="缺陷定位图" />
        <div
          v-for="(tiao, suoyin) in qingdanYouKuang"
          :key="suoyin"
          class="dingwei_kuang"
          :style="kuangYangshi(tiao.jiankuang)"
        >
          <span class="kuang_biaoqian" :style="{ background: kuangYanse(tiao.leixing) }">
            {{ kuangWenzi(tiao) }}
          </span>
        </div>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 道路状况 -->
      <el-col :span="12">
        <div class="ziduan_kapian">
          <div class="ziduan_toubu">
            <el-icon class="ziduan_tubiao" color="#409eff"><OfficeBuilding /></el-icon>
            <span class="ziduan_mingcheng">道路状况</span>
          </div>
          <div class="ziduan_neirong">{{ huoquZiduan('daolu_zhuangkuang') }}</div>
        </div>
      </el-col>

      <!-- 缺陷类型 -->
      <el-col :span="12">
        <div class="ziduan_kapian">
          <div class="ziduan_toubu">
            <el-icon class="ziduan_tubiao" color="#e6a23c"><Warning /></el-icon>
            <span class="ziduan_mingcheng">缺陷类型</span>
          </div>
          <div class="ziduan_neirong">{{ huoquZiduan('queshi_leixing') }}</div>
        </div>
      </el-col>

      <!-- 严重程度 -->
      <el-col :span="12">
        <div class="ziduan_kapian">
          <div class="ziduan_toubu">
            <el-icon class="ziduan_tubiao" :color="yanzchengduYanse.yanse">
              <ScaleToOriginal />
            </el-icon>
            <span class="ziduan_mingcheng">严重程度</span>
          </div>
          <div class="ziduan_neirong">
            <el-tag
              :type="yanzchengduYanse.leixing"
              effect="dark"
              size="large"
            >
              {{ huoquZiduan('yansong_chengdu') || '无' }}
            </el-tag>
          </div>
        </div>
      </el-col>

      <!-- 紧急程度 -->
      <el-col :span="12">
        <div class="ziduan_kapian">
          <div class="ziduan_toubu">
            <el-icon class="ziduan_tubiao" :color="jinchengduYanse.yanse">
              <Timer />
            </el-icon>
            <span class="ziduan_mingcheng">紧急程度</span>
          </div>
          <div class="ziduan_neirong">
            <el-tag
              :type="jinchengduYanse.leixing"
              effect="dark"
              size="large"
            >
              {{ huoquZiduan('yingji_chengdu') || '无' }}
            </el-tag>
          </div>
        </div>
      </el-col>

      <!-- 缺陷位置 -->
      <el-col :span="24">
        <div class="ziduan_kapian">
          <div class="ziduan_toubu">
            <el-icon class="ziduan_tubiao" color="#67c23a"><LocationInformation /></el-icon>
            <span class="ziduan_mingcheng">缺陷位置</span>
          </div>
          <div class="ziduan_neirong">{{ huoquZiduan('queshi_weizhi') }}</div>
        </div>
      </el-col>

      <!-- 修复建议 -->
      <el-col :span="24">
        <div class="ziduan_kapian">
          <div class="ziduan_toubu">
            <el-icon class="ziduan_tubiao" color="#909399"><Tools /></el-icon>
            <span class="ziduan_mingcheng">修复建议</span>
          </div>
          <div class="ziduan_neirong">{{ huoquZiduan('chuli_jianyi') }}</div>
        </div>
      </el-col>

      <!-- 所需材料 -->
      <el-col :span="24">
        <div class="ziduan_kapian">
          <div class="ziduan_toubu">
            <el-icon class="ziduan_tubiao" color="#9c27b0"><Box /></el-icon>
            <span class="ziduan_mingcheng">所需材料</span>
          </div>
          <div class="ziduan_neirong">
            <template v-if="cailiaoLiebiao.length">
              <el-tag
                v-for="(cailiao, suoyin) in cailiaoLiebiao"
                :key="suoyin"
                class="cailiao_biaoqian"
                type="info"
                effect="plain"
              >
                {{ cailiao }}
              </el-tag>
            </template>
            <span v-else>{{ huoquZiduan('suo_xu_cailiao') }}</span>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// 接收 AI 分析结果对象与巡检图片地址
const props = defineProps({
  aiResult: {
    type: Object,
    default: () => ({}),
  },
  imageUrl: {
    type: String,
    default: '',
  },
})

// 缺陷框按类型配色
const KUANG_YANSE = {
  坑洞: '#f56c6c',
  龟裂: '#f56c6c',
  裂缝: '#e6a23c',
  车辙: '#9c27b0',
  松散: '#409eff',
  修补痕迹: '#67c23a',
}

// 获取字段值，支持拼音和中文 key 兼容
function huoquZiduan(ziduan_ming) {
  const jieguo = props.aiResult || {}
  return jieguo[ziduan_ming] ?? jieguo[zhongwen_map[ziduan_ming]] ?? '暂无数据'
}

// 拼音字段名到中文字段名的映射
const zhongwen_map = {
  daolu_zhuangkuang: '道路状况',
  queshi_leixing: '缺陷类型',
  yansong_chengdu: '严重程度',
  queshi_weizhi: '缺陷位置',
  chuli_jianyi: '修复建议',
  suo_xu_cailiao: '所需材料',
  yingji_chengdu: '紧急程度',
}

// 严重程度对应颜色
const yanzchengduYanse = computed(() => {
  const zhi = huoquZiduan('yansong_chengdu')
  if (zhi === '严重' || zhi === '高') return { leixing: 'danger', yanse: '#f56c6c' }
  if (zhi === '中等' || zhi === '中') return { leixing: 'warning', yanse: '#e6a23c' }
  if (zhi === '轻微' || zhi === '低') return { leixing: 'success', yanse: '#67c23a' }
  return { leixing: 'info', yanse: '#909399' }
})

// 紧急程度对应颜色
const jinchengduYanse = computed(() => {
  const zhi = huoquZiduan('yingji_chengdu')
  if (zhi === '立即封路' || zhi === '严重' || zhi === '高') return { leixing: 'danger', yanse: '#f56c6c' }
  if (zhi === '建议绕行' || zhi === '中等') return { leixing: 'warning', yanse: '#e6a23c' }
  if (zhi === '低速行驶通过' || zhi === '轻微') return { leixing: 'success', yanse: '#67c23a' }
  return { leixing: 'info', yanse: '#909399' }
})

// 所需材料列表（支持数组或字符串）
const cailiaoLiebiao = computed(() => {
  const cailiao = huoquZiduan('suo_xu_cailiao')
  if (Array.isArray(cailiao)) return cailiao
  if (typeof cailiao === 'string' && cailiao.includes('、')) {
    return cailiao.split('、').filter((s) => s.trim())
  }
  return []
})

// 缺陷清单（模型输出的逐缺陷定位数据）
const qingdanLiebiao = computed(() => {
  const qingdan = props.aiResult?.quexian_qingdan
  return Array.isArray(qingdan) ? qingdan : []
})

// 带有效边界框的缺陷条目
const qingdanYouKuang = computed(() => {
  return qingdanLiebiao.value.filter((tiao) => {
    return tiao && Array.isArray(tiao.jiankuang) && tiao.jiankuang.length === 4
  })
})

// 是否展示画框图（有图且有可画框的缺陷）
const youDingweiTu = computed(() => {
  return Boolean(props.imageUrl) && qingdanYouKuang.value.length > 0
})

// 根据归一化边界框生成叠加框样式
// 处理三件事：坐标交换、过小框放大显示、边界钳制到图片范围内
function kuangYangshi(jiankuang) {
  let x1 = jiankuang[0]
  let y1 = jiankuang[1]
  let x2 = jiankuang[2]
  let y2 = jiankuang[3]
  if (x1 > x2) [x1, x2] = [x2, x1]
  if (y1 > y2) [y1, y2] = [y2, y1]

  // 最小显示尺寸（百分比），小于该值的框放大显示，便于观察小缺陷
  const ZUIXIAO = 1.8
  let kuan = (x2 - x1) * 100
  let gao = (y2 - y1) * 100
  let zuo = x1 * 100
  let ding = y1 * 100

  if (kuan < ZUIXIAO) {
    zuo = zuo + kuan / 2 - ZUIXIAO / 2
    kuan = ZUIXIAO
  }
  if (gao < ZUIXIAO) {
    ding = ding + gao / 2 - ZUIXIAO / 2
    gao = ZUIXIAO
  }

  // 钳制到图片范围内，避免框超出容器
  zuo = Math.max(0, Math.min(100 - kuan, zuo))
  ding = Math.max(0, Math.min(100 - gao, ding))

  return {
    left: `${zuo.toFixed(2)}%`,
    top: `${ding.toFixed(2)}%`,
    width: `${kuan.toFixed(2)}%`,
    height: `${gao.toFixed(2)}%`,
  }
}

// 缺陷类型对应框颜色
function kuangYanse(leixing) {
  return KUANG_YANSE[leixing] || '#f56c6c'
}

// 框标签文字：类型 + 尺寸估计
function kuangWenzi(tiao) {
  const chiCun = tiao.chicun_gu_ji || ''
  return tiao.leixing + (chiCun ? ` ${chiCun}` : '')
}
</script>

<style scoped>
.ai_jieguo_rongqi {
  width: 100%;
}

/* 缺陷定位画框区块 */
.dingwei_kuai {
  margin-bottom: 16px;
}

.dingwei_tou {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #f56c6c;
  margin-bottom: 8px;
}

.tupian_dingwei {
  position: relative;
  display: block;
  width: 100%;
  max-height: 70vh;
  overflow: auto;
  background: #f5f7fa;
  border-radius: 8px;
}

.dingwei_tu {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 6px;
  cursor: zoom-in;
}

.dingwei_kuang {
  position: absolute;
  border: 2px solid #f56c6c;
  border-radius: 4px;
  box-sizing: border-box;
  pointer-events: none;
}

.kuang_biaoqian {
  position: absolute;
  top: 2px;
  left: 2px;
  display: inline-block;
  padding: 1px 6px;
  font-size: 12px;
  line-height: 1.6;
  color: #fff;
  border-radius: 3px;
  white-space: nowrap;
}

.ziduan_kapian {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 16px;
  transition: all 0.3s;
}

.ziduan_kapian:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border-color: #c6e2ff;
}

.ziduan_toubu {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.ziduan_tubiao {
  font-size: 18px;
}

.ziduan_mingcheng {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.ziduan_neirong {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  word-break: break-all;
}

.cailiao_biaoqian {
  margin-right: 8px;
  margin-bottom: 8px;
}
</style>
