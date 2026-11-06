<template>
  <div class="xinxun_yemian">
    <el-row :gutter="20">
      <!-- 左侧上传区域 -->
      <el-col :xs="24" :lg="10">
        <el-card shadow="hover">
          <template #header>
            <div class="kapian_tou">
              <el-icon><Upload /></el-icon>
              <span>上传巡检图片</span>
            </div>
          </template>

          <el-form label-width="90px" label-position="right">
            <el-form-item label="道路点位">
              <el-select
                v-model="dangqian_daolu"
                placeholder="请选择道路点位"
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
          </el-form>

          <!-- 图片上传区域 -->
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
              <div class="shangchuan_wenzi">将图片拖到此处，或<em>点击上传</em></div>
              <div class="shangchuan_tishi">支持 JPG、PNG 格式，文件不超过 10MB</div>
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
              @click="kaishiFenxi"
            >
              <el-icon v-if="!fenxi_jiazai"><Cpu /></el-icon>
              {{ fenxi_jiazai ? 'AI 分析中...' : '开始 AI 分析' }}
            </el-button>
          </div>

          <!-- 分析进度提示 -->
          <el-alert
            v-if="fenxi_jiazai"
            title="AI 正在分析图片，请耐心等待..."
            type="info"
            :closable="false"
            show-icon
            class="jindu_tishi"
          />
        </el-card>
      </el-col>

      <!-- 右侧 AI 分析结果 -->
      <el-col :xs="24" :lg="14">
        <el-card shadow="hover">
          <template #header>
            <div class="kapian_tou">
              <el-icon><Cpu /></el-icon>
              <span>AI 智能分析结果</span>
            </div>
          </template>

          <!-- 空状态 -->
          <el-empty v-if="!ai_jieguo && !fenxi_jiazai" description="上传图片后将显示 AI 分析结果">
            <template #image>
              <el-icon :size="60" color="#c0c4cc"><Picture /></el-icon>
            </template>
          </el-empty>

          <!-- 加载中 -->
          <div v-else-if="fenxi_jiazai" class="fenxi_jiazai">
            <el-skeleton :rows="8" animated />
          </div>

          <!-- 分析结果 -->
          <AiResultCard v-else :ai-result="ai_jieguo" :image-url="fenxi_tupian_url" />

          <!-- 自动生成工单提示 -->
          <el-alert
            v-if="ai_jieguo && zidong_gongdan"
            title="系统已根据缺陷严重程度自动生成处置工单"
            type="success"
            show-icon
            :closable="false"
            class="gongdan_tishi"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { chuangjianXunjian, huoquDaoluLiebiao } from '../api'
import AiResultCard from '../components/AiResultCard.vue'

// 道路列表
const daolu_liebiao = ref([])
const dangqian_daolu = ref(null)
const daolu_jiazai = ref(false)

// 上传相关
const shangchuanRef = ref(null)
const xuanze_wenjian = ref(null)
const yulan_tupian = ref('')

// 分析状态
const fenxi_jiazai = ref(false)
const ai_jieguo = ref(null)
const zidong_gongdan = ref(false)
// 分析用图片地址（供结果卡片叠加画框）
const fenxi_tupian_url = ref('')

// 加载道路列表
async function jiazaiDaolu() {
  daolu_jiazai.value = true
  try {
    const jieguo = await huoquDaoluLiebiao()
    // 兼容返回格式：可能是数组，也可能是 { sites: [...] } 或 { roads: [...] }
    if (Array.isArray(jieguo)) {
      daolu_liebiao.value = jieguo
    } else if (jieguo.roads) {
      daolu_liebiao.value = jieguo.roads
    } else if (jieguo.sites) {
      // 后端按区域分组返回的情况，需要展开
      const zhankai = []
      jieguo.sites.forEach((quyu) => {
        if (quyu.children) {
          quyu.children.forEach((dianwei) => zhankai.push(dianwei))
        }
      })
      daolu_liebiao.value = zhankai
    } else {
      daolu_liebiao.value = []
    }
  } catch (cuowu) {
    ElMessage.warning('道路列表加载失败')
  } finally {
    daolu_jiazai.value = false
  }
}

// 文件选择变化
function wenjianBianhua(wenjian) {
  const tupian = wenjian.raw
  if (!tupian) return

  // 校验文件类型
  const leixing = tupian.type
  if (!leixing.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }

  // 校验文件大小（10MB）
  if (tupian.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB')
    return
  }

  xuanze_wenjian.value = tupian
  yulan_tupian.value = URL.createObjectURL(tupian)
  // 清除之前的分析结果
  ai_jieguo.value = null
  zidong_gongdan.value = false
}

// 重新选择图片
function chongxinXuanze() {
  xuanze_wenjian.value = null
  yulan_tupian.value = ''
  ai_jieguo.value = null
  zidong_gongdan.value = false
  fenxi_tupian_url.value = ''
  if (shangchuanRef.value) {
    shangchuanRef.value.clearFiles()
  }
}

// 开始 AI 分析
async function kaishiFenxi() {
  if (!xuanze_wenjian.value) {
    ElMessage.warning('请先选择巡检图片')
    return
  }

  fenxi_jiazai.value = true
  ai_jieguo.value = null
  fenxi_tupian_url.value = ''

  try {
    const biaodan = new FormData()
    biaodan.append('tupian', xuanze_wenjian.value)
    if (dangqian_daolu.value) {
      biaodan.append('road_id', dangqian_daolu.value)
    }

    const jieguo = await chuangjianXunjian(biaodan)
    ai_jieguo.value = jieguo.ai_result || jieguo
    // 后端返回的图片地址用于画框展示
    fenxi_tupian_url.value = jieguo.image_url || ''
    zidong_gongdan.value = jieguo.auto_workorder || false
    ElMessage.success(jieguo.message || 'AI 分析完成')
  } catch (cuowu) {
    const cuowu_xinxi = cuowu.message || ''
    if (cuowu_xinxi.includes('timeout')) {
      ElMessage.error('AI 分析超时，请稍后重试')
    } else {
      ElMessage.error(cuowu_xinxi || 'AI 分析失败，请重试')
    }
  } finally {
    fenxi_jiazai.value = false
  }
}

onMounted(() => {
  jiazaiDaolu()
})
</script>

<style scoped>
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

/* 上传区域 */
.shangchuan_qu {
  width: 100%;
}

.shangchuan_qu :deep(.el-upload-dragger) {
  width: 100%;
  padding: 30px 20px;
}

.shangchuan_zhanwei {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.shangchuan_tubiao {
  font-size: 48px;
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

/* 图片预览 */
.yulan_qu {
  position: relative;
  display: inline-block;
}

.yulan_tu {
  max-width: 100%;
  max-height: 300px;
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
  margin-top: 20px;
  text-align: center;
}

.caozuo_anniu .el-button {
  width: 100%;
}

.jindu_tishi {
  margin-top: 16px;
}

.gongdan_tishi {
  margin-top: 16px;
}
</style>
