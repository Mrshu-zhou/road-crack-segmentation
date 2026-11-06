<template>
  <div class="fenge_yemian">
    <el-row :gutter="20">
      <!-- 左侧：上传与控制 -->
      <el-col :xs="24" :lg="9">
        <el-card shadow="hover">
          <template #header>
            <div class="kapian_tou">
              <el-icon><Cpu /></el-icon>
              <span>裂缝像素级分割</span>
            </div>
          </template>

          <el-form label-width="96px" label-position="right">
            <el-form-item label="道路点位">
              <el-select
                v-model="dangqian_daolu"
                placeholder="可选，保存巡检时使用"
                filterable
                clearable
                style="width: 100%"
                :loading="daolu_jiazai"
              >
                <el-option
                  v-for="daolu in daolu_liebiao"
                  :key="daolu.id"
                  :label="daolu.road_name + (daolu.section ? ' - ' + daolu.section : '')"
                  :value="daolu.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="分割模型">
              <el-select v-model="moxing_xuanze" style="width: 100%">
                <el-option label="DeepLabV3+ (MobileNetV2)" value="deeplabv3plus_mobilenetv2" />
                <el-option label="SegFormer-B0" value="segformer_b0" />
                <el-option label="双模型对比" value="compare" />
              </el-select>
            </el-form-item>

            <el-form-item label="标定比例">
              <el-input-number
                v-model="mm_per_pixel"
                :min="0.1"
                :max="20"
                :step="0.1"
                :precision="2"
                style="width: 100%"
              />
              <div class="biaoding_tishi">毫米 / 像素，用于长度与宽度换算</div>
            </el-form-item>

            <el-form-item label="预处理">
              <el-select v-model="yuchuli_moshi" style="width: 100%">
                <el-option label="自动（按模型训练配置）" value="auto" />
                <el-option label="无预处理（基线）" value="none" />
                <el-option label="CLAHE + 双边滤波" value="clahe" />
                <el-option label="CLAHE + Retinex + 反锐化" value="full" />
              </el-select>
            </el-form-item>
          </el-form>

          <el-upload
            ref="shangchuanRef"
            class="shangchuan_qu"
            drag
            :auto-upload="false"
            :show-file-list="false"
            :on-change="wenjianBianhua"
            accept="image/*"
          >
            <div v-if="!yulan_tupian" class="shangchuan_zhanwei">
              <el-icon class="shangchuan_tubiao"><UploadFilled /></el-icon>
              <div class="shangchuan_wenzi">将裂缝图片拖到此处，或<em>点击上传</em></div>
              <div class="shangchuan_tishi">支持 JPG、PNG，文件不超过 10MB</div>
            </div>
            <div v-else class="yulan_qu">
              <img :src="yulan_tupian" class="yulan_tu" alt="预览图" />
              <div class="yulan_zhezhao">
                <el-button type="primary" link @click.stop="chongxinXuanze">
                  <el-icon><Refresh /></el-icon>
                  重新选择
                </el-button>
              </div>
            </div>
          </el-upload>

          <div class="caozuo_anniu">
            <el-button
              type="primary"
              size="large"
              :loading="fenxi_jiazai"
              :disabled="!xuanze_wenjian"
              @click="kaishiFenge"
            >
              <el-icon v-if="!fenxi_jiazai"><Aim /></el-icon>
              {{ fenxi_jiazai ? '分割推理中...' : '开始分割' }}
            </el-button>
            <el-button
              size="large"
              :loading="yuchuli_jiazai"
              :disabled="!xuanze_wenjian"
              @click="kaishiYuchuli"
            >
              预处理对比
            </el-button>
          </div>

          <el-alert
            v-if="fenxi_jiazai"
            title="正在执行预处理、分割推理与量化定级..."
            type="info"
            :closable="false"
            show-icon
            class="jindu_tishi"
          />

          <div class="moxing_zhuangtai">
            <span class="zhuangtai_biaoti">权重状态：</span>
            <el-tag
              v-for="moxing in moxing_liebiao"
              :key="moxing.model_key"
              :type="moxing.available ? 'success' : 'info'"
              size="small"
              effect="plain"
              class="moxing_biaoqian"
            >
              {{ moxing.label }} {{ moxing.available ? '可用' : '未训练' }}
            </el-tag>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：结果展示 -->
      <el-col :xs="24" :lg="15">
        <el-card shadow="hover" class="jieguo_kapian">
          <template #header>
            <div class="kapian_tou">
              <el-icon><Picture /></el-icon>
              <span>分割与量化结果</span>
            </div>
          </template>

          <el-empty v-if="!jieguo_liebiao.length && !fenxi_jiazai" description="上传图片后开始分割">
            <template #image>
              <el-icon :size="60" color="#c0c4cc"><Aim /></el-icon>
            </template>
          </el-empty>

          <div v-else-if="fenxi_jiazai" class="fenxi_jiazai">
            <el-skeleton :rows="8" animated />
          </div>

          <el-row v-else :gutter="16">
            <el-col
              v-for="(jieguo, suoyin) in jieguo_liebiao"
              :key="suoyin"
              :xs="24"
              :lg="jieguo_liebiao.length > 1 ? 12 : 24"
            >
              <el-card shadow="never" class="dange_jieguo">
                <template #header>
                  <div class="jieguo_tou">
                    <el-tag type="primary" effect="dark" size="small">{{ jieguo.model_label }}</el-tag>
                    <el-tag size="small" effect="plain">{{ jieguo.preprocess_mode }}</el-tag>
                    <span class="haoshi">{{ jieguo.latency_ms }} ms</span>
                  </div>
                </template>

                <el-alert
                  v-if="jieguo.error"
                  :title="jieguo.error"
                  type="error"
                  :closable="false"
                  show-icon
                />

                <template v-else>
                  <el-row :gutter="10" class="tupian_duibi">
                    <el-col :span="12">
                      <div class="tupian_biaoti">缺陷叠加图</div>
                      <el-image
                        :src="tupianDizhi(jieguo.overlay_url)"
                        fit="contain"
                        class="jieguo_tu"
                        :preview-src-list="[tupianDizhi(jieguo.overlay_url)]"
                        preview-teleported
                      />
                    </el-col>
                    <el-col :span="12">
                      <div class="tupian_biaoti">分割掩码</div>
                      <el-image
                        :src="tupianDizhi(jieguo.mask_url)"
                        fit="contain"
                        class="jieguo_tu"
                        :preview-src-list="[tupianDizhi(jieguo.mask_url)]"
                        preview-teleported
                      />
                    </el-col>
                  </el-row>

                  <div class="shuzhi_ge">
                    <div class="shuzhi_kapian">
                      <div class="shuzhi_shu">{{ jieguo.quantification.defect_count }}</div>
                      <div class="shuzhi_ming">裂缝处数</div>
                    </div>
                    <div class="shuzhi_kapian">
                      <div class="shuzhi_shu">{{ geShi(jieguo.quantification.length_mm) }}</div>
                      <div class="shuzhi_ming">累计长度 mm</div>
                    </div>
                    <div class="shuzhi_kapian">
                      <div class="shuzhi_shu">{{ geShi(jieguo.quantification.width_max_mm) }}</div>
                      <div class="shuzhi_ming">最大宽度 mm</div>
                    </div>
                    <div class="shuzhi_kapian">
                      <div class="shuzhi_shu">{{ geShi(jieguo.quantification.area_ratio * 100, 2) }}%</div>
                      <div class="shuzhi_ming">面积占比</div>
                    </div>
                  </div>

                  <el-descriptions :column="2" border size="small" class="jieguo_miaoshu">
                    <el-descriptions-item label="严重程度">
                      <el-tag :type="yanzhongLeixing(jieguo.yansong_chengdu)" effect="dark" size="small">
                        {{ jieguo.yansong_chengdu }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="紧急程度">
                      <el-tag :type="yingjiLeixing(jieguo.yingji_chengdu)" size="small">
                        {{ jieguo.yingji_chengdu }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="分级依据" :span="2">
                      {{ jieguo.yansong_yiju || '按裂缝宽度阈值分级' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="修复建议" :span="2">
                      {{ jieguo.chuli_jianyi }}
                    </el-descriptions-item>
                    <el-descriptions-item label="平均宽度">
                      {{ geShi(jieguo.quantification.width_mean_mm) }} mm
                    </el-descriptions-item>
                    <el-descriptions-item label="裂缝面积">
                      {{ geShi(jieguo.quantification.area_mm2, 0) }} mm²
                    </el-descriptions-item>
                  </el-descriptions>
                </template>
              </el-card>
            </el-col>
          </el-row>

          <div v-if="jieguo_liebiao.length" class="baocun_qu">
            <el-button
              type="success"
              :loading="baocun_jiazai"
              :disabled="jieguo_liebiao.length > 1"
              @click="baocunXunjian"
            >
              <el-icon><DocumentAdd /></el-icon>
              保存为巡检记录
            </el-button>
            <span v-if="jieguo_liebiao.length > 1" class="baocun_tishi">
              双模型对比模式请先选择单个模型再保存
            </span>
          </div>

          <el-alert
            v-if="baocun_jieguo"
            :title="baocun_jieguo"
            :type="zidong_gongdan ? 'success' : 'info'"
            show-icon
            :closable="false"
            class="gongdan_tishi"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 预处理对比 -->
    <el-card v-if="yuchuli_jieguo" shadow="hover" class="yuchuli_kapian">
      <template #header>
        <div class="kapian_tou">
          <el-icon><MagicStick /></el-icon>
          <span>图像预处理与增强对比</span>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col v-for="moshi in yuchuli_moshi_liebiao" :key="moshi.key" :xs="24" :sm="8">
          <div class="yuchuli_xiang">
            <div class="tupian_biaoti">{{ moshi.label }}</div>
            <el-image
              :src="tupianDizhi(yuchuli_jieguo.urls[moshi.key])"
              fit="contain"
              class="yuchuli_tu"
              :preview-src-list="[tupianDizhi(yuchuli_jieguo.urls[moshi.key])]"
              preview-teleported
            />
            <el-descriptions :column="2" size="small" border class="yuchuli_shuju">
              <el-descriptions-item label="亮度">
                {{ geShi(yuchuli_jieguo.stats[moshi.key]?.brightness) }}
              </el-descriptions-item>
              <el-descriptions-item label="对比度">
                {{ geShi(yuchuli_jieguo.stats[moshi.key]?.contrast) }}
              </el-descriptions-item>
              <el-descriptions-item label="阴影占比">
                {{ geShi((yuchuli_jieguo.stats[moshi.key]?.shadow_ratio || 0) * 100, 1) }}%
              </el-descriptions-item>
              <el-descriptions-item label="清晰度">
                {{ geShi(yuchuli_jieguo.stats[moshi.key]?.sharpness) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 实验指标 -->
    <el-card shadow="hover" class="shiyan_kapian">
      <template #header>
        <div class="kapian_tou">
          <el-icon><DataAnalysis /></el-icon>
          <span>模型对比与消融实验</span>
        </div>
      </template>

      <el-empty v-if="!shiyan_jieguo.models || !shiyan_jieguo.models.length" description="完成训练与评估后显示实验指标" />

      <template v-else>
        <div ref="shiyan_tubiao" class="shiyan_tubiao"></div>
        <el-table :data="shiyan_jieguo.ablation || []" size="small" border stripe class="xiaoRong_table">
          <el-table-column prop="group" label="实验组" width="110" />
          <el-table-column prop="name" label="配置" min-width="150" />
          <el-table-column prop="iou" label="IoU" width="100" />
          <el-table-column prop="dice" label="Dice" width="100" />
          <el-table-column prop="boundary_iou" label="边界 IoU" width="110" />
          <el-table-column prop="note" label="说明" min-width="180" show-overflow-tooltip />
        </el-table>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  duibiFenge,
  fenxiFenge,
  huoquDaoluLiebiao,
  huoquFengeMoxing,
  huoquFengeShiyan,
  yuchuliDuibi,
} from '../api'

const daolu_liebiao = ref([])
const dangqian_daolu = ref(null)
const daolu_jiazai = ref(false)

const shangchuanRef = ref(null)
const xuanze_wenjian = ref(null)
const yulan_tupian = ref('')

const moxing_xuanze = ref('deeplabv3plus_mobilenetv2')
const mm_per_pixel = ref(1.0)
const yuchuli_moshi = ref('auto')

const fenxi_jiazai = ref(false)
const yuchuli_jiazai = ref(false)
const baocun_jiazai = ref(false)

const jieguo_liebiao = ref([])
const yuchuli_jieguo = ref(null)
const baocun_jieguo = ref('')
const zidong_gongdan = ref(false)

const moxing_liebiao = ref([])
const shiyan_jieguo = ref({ models: [], ablation: [] })
const shiyan_tubiao = ref(null)
let shiyan_chart = null

const yuchuli_moshi_liebiao = [
  { key: 'none', label: '原始图像（none）' },
  { key: 'clahe', label: 'CLAHE + 双边滤波' },
  { key: 'full', label: 'CLAHE + Retinex + 反锐化' },
]

function geShi(shuzhi, weishu = 1) {
  if (shuzhi === null || shuzhi === undefined || Number.isNaN(Number(shuzhi))) return '-'
  return Number(shuzhi).toFixed(weishu)
}

function tupianDizhi(lujing) {
  if (!lujing) return ''
  if (lujing.startsWith('http')) return lujing
  return lujing.replace(/^.*uploads/, '/uploads')
}

function yanzhongLeixing(zhi) {
  if (zhi === '严重') return 'danger'
  if (zhi === '中等') return 'warning'
  if (zhi === '轻微') return 'success'
  return 'info'
}

function yingjiLeixing(zhi) {
  if (zhi === '立即封路') return 'danger'
  if (zhi === '建议绕行') return 'warning'
  if (zhi === '低速行驶通过') return 'success'
  return 'info'
}

async function jiazaiDaolu() {
  daolu_jiazai.value = true
  try {
    const jieguo = await huoquDaoluLiebiao()
    if (Array.isArray(jieguo)) {
      daolu_liebiao.value = jieguo
    } else if (jieguo.roads) {
      daolu_liebiao.value = jieguo.roads
    } else {
      daolu_liebiao.value = []
    }
  } catch {
    ElMessage.warning('道路列表加载失败')
  } finally {
    daolu_jiazai.value = false
  }
}

async function jiazaiMoxing() {
  try {
    const jieguo = await huoquFengeMoxing()
    moxing_liebiao.value = jieguo.items || []
  } catch {
    moxing_liebiao.value = []
  }
}

async function jiazaiShiyan() {
  try {
    shiyan_jieguo.value = await huoquFengeShiyan()
  } catch {
    shiyan_jieguo.value = { models: [], ablation: [] }
  }
  await nextTick()
  huiZhiShiyan()
}

function huiZhiShiyan() {
  if (!shiyan_tubiao.value || !shiyan_jieguo.value.models?.length) return
  if (!shiyan_chart) {
    shiyan_chart = echarts.init(shiyan_tubiao.value)
  }
  const fenlei = ['DeepCrack IoU', 'DeepCrack Dice', 'CFD IoU', 'CFD Dice']
  const xilie = shiyan_jieguo.value.models.map((moxing) => ({
    name: moxing.label,
    type: 'bar',
    barWidth: 18,
    data: [
      moxing.deepcrack?.iou || 0,
      moxing.deepcrack?.dice || 0,
      moxing.cfd?.iou || 0,
      moxing.cfd?.dice || 0,
    ],
  }))
  shiyan_chart.setOption({
    tooltip: { trigger: 'axis', valueFormatter: (zhi) => Number(zhi).toFixed(4) },
    legend: { bottom: 0 },
    grid: { left: '8%', right: '4%', top: 24, bottom: 48 },
    xAxis: { type: 'category', data: fenlei, axisLabel: { interval: 0 } },
    yAxis: { type: 'value', min: 0, max: 1, name: '指标值' },
    series: xilie,
    color: ['#409eff', '#67c23a'],
  })
}

function wenjianBianhua(wenjian) {
  const tupian = wenjian.raw
  if (!tupian) return
  if (!tupian.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  if (tupian.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB')
    return
  }
  xuanze_wenjian.value = tupian
  yulan_tupian.value = URL.createObjectURL(tupian)
  jieguo_liebiao.value = []
  yuchuli_jieguo.value = null
  baocun_jieguo.value = ''
}

function chongxinXuanze() {
  xuanze_wenjian.value = null
  yulan_tupian.value = ''
  jieguo_liebiao.value = []
  yuchuli_jieguo.value = null
  baocun_jieguo.value = ''
  if (shangchuanRef.value) {
    shangchuanRef.value.clearFiles()
  }
}

function goujianBiaodan() {
  const biaodan = new FormData()
  biaodan.append('tupian', xuanze_wenjian.value)
  biaodan.append('mm_per_pixel', mm_per_pixel.value)
  if (yuchuli_moshi.value !== 'auto') {
    biaodan.append('preprocess', yuchuli_moshi.value)
  }
  return biaodan
}

async function kaishiFenge() {
  if (!xuanze_wenjian.value) {
    ElMessage.warning('请先选择图片')
    return
  }
  fenxi_jiazai.value = true
  jieguo_liebiao.value = []
  baocun_jieguo.value = ''
  try {
    const biaodan = goujianBiaodan()
    if (moxing_xuanze.value === 'compare') {
      const jieguo = await duibiFenge(biaodan)
      jieguo_liebiao.value = jieguo.results || []
    } else {
      biaodan.append('model_key', moxing_xuanze.value)
      const jieguo = await fenxiFenge(biaodan)
      jieguo_liebiao.value = [jieguo.result]
    }
    ElMessage.success('分割完成')
  } catch (cuowu) {
    ElMessage.error(cuowu.message || '分割失败')
  } finally {
    fenxi_jiazai.value = false
  }
}

async function kaishiYuchuli() {
  if (!xuanze_wenjian.value) {
    ElMessage.warning('请先选择图片')
    return
  }
  yuchuli_jiazai.value = true
  try {
    const biaodan = new FormData()
    biaodan.append('tupian', xuanze_wenjian.value)
    yuchuli_jieguo.value = await yuchuliDuibi(biaodan)
  } catch (cuowu) {
    ElMessage.error(cuowu.message || '预处理对比失败')
  } finally {
    yuchuli_jiazai.value = false
  }
}

async function baocunXunjian() {
  if (!xuanze_wenjian.value || jieguo_liebiao.value.length !== 1) return
  baocun_jiazai.value = true
  try {
    const biaodan = goujianBiaodan()
    biaodan.append('model_key', jieguo_liebiao.value[0].model_key)
    if (dangqian_daolu.value) {
      biaodan.append('road_id', dangqian_daolu.value)
    }
    biaodan.append('save_inspection', 'true')
    const jieguo = await fenxiFenge(biaodan)
    baocun_jieguo.value = `已生成巡检记录 #${jieguo.id}`
    zidong_gongdan.value = jieguo.auto_workorder || false
    ElMessage.success('巡检记录已保存')
  } catch (cuowu) {
    ElMessage.error(cuowu.message || '保存失败')
  } finally {
    baocun_jiazai.value = false
  }
}

function chuangkouBianhua() {
  shiyan_chart?.resize()
}

onMounted(() => {
  jiazaiDaolu()
  jiazaiMoxing()
  jiazaiShiyan()
  window.addEventListener('resize', chuangkouBianhua)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', chuangkouBianhua)
  shiyan_chart?.dispose()
})
</script>

<style scoped>
.fenge_yemian {
  display: flex;
  flex-direction: column;
  gap: 20px;
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

.shangchuan_qu {
  width: 100%;
}

.shangchuan_qu :deep(.el-upload-dragger) {
  width: 100%;
  padding: 26px 20px;
}

.shangchuan_zhanwei {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.shangchuan_tubiao {
  font-size: 44px;
  color: #c0c4cc;
}

.shangchuan_wenzi {
  font-size: 14px;
  color: #606266;
}

.shangchuan_wenzi em {
  color: #409eff;
  font-style: normal;
}

.shangchuan_tishi {
  font-size: 12px;
  color: #909399;
}

.yulan_qu {
  position: relative;
  display: inline-block;
}

.yulan_tu {
  max-width: 100%;
  max-height: 260px;
  border-radius: 6px;
}

.yulan_zhezhao {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 0 0 6px 6px;
  text-align: center;
  padding: 8px;
}

.caozuo_anniu {
  margin-top: 18px;
  display: flex;
  gap: 10px;
}

.caozuo_anniu .el-button {
  flex: 1;
}

.biaoding_tishi {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-top: 2px;
}

.jindu_tishi {
  margin-top: 14px;
}

.moxing_zhuangtai {
  margin-top: 14px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.zhuangtai_biaoti {
  font-size: 12px;
  color: #909399;
}

.moxing_biaoqian {
  margin-right: 2px;
}

.jieguo_tou {
  display: flex;
  align-items: center;
  gap: 8px;
}

.haoshi {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}

.tupian_duibi {
  margin-bottom: 14px;
}

.tupian_biaoti {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 6px;
}

.jieguo_tu {
  width: 100%;
  height: 220px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: zoom-in;
}

.shuzhi_ge {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}

.shuzhi_kapian {
  background: linear-gradient(135deg, #eef5ff, #f7fbff);
  border: 1px solid #d9ecff;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.shuzhi_shu {
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
}

.shuzhi_ming {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.jieguo_miaoshu {
  margin-top: 4px;
}

.baocun_qu {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.baocun_tishi {
  font-size: 12px;
  color: #909399;
}

.gongdan_tishi {
  margin-top: 14px;
}

.yuchuli_kapian {
  margin-top: 0;
}

.yuchuli_xiang {
  margin-bottom: 12px;
}

.yuchuli_tu {
  width: 100%;
  height: 180px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: zoom-in;
}

.yuchuli_shuju {
  margin-top: 8px;
}

.shiyan_tubiao {
  width: 100%;
  height: 320px;
}

.xiaoRong_table {
  margin-top: 16px;
}
</style>
