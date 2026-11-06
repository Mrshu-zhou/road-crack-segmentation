import axios from 'axios'

// 创建 axios 请求实例
// 超时时间 200 秒：AI 分析可能经历重试，需留足缓冲
const qingqiu_shili = axios.create({
  baseURL: '/api',
  timeout: 200000,
})

// 请求拦截器：自动携带 Authorization 令牌
qingqiu_shili.interceptors.request.use(
  (config) => {
    const lingpai = localStorage.getItem('lingpai')
    if (lingpai) {
      config.headers.Authorization = `Bearer ${lingpai}`
    }
    return config
  },
  (cuowu) => Promise.reject(cuowu),
)

// 响应拦截器：统一错误处理，401 自动跳转登录
qingqiu_shili.interceptors.response.use(
  (response) => response.data,
  (cuowu) => {
    let cuowu_xinxi = '请求失败'
    const xiangqing = cuowu.response?.data?.detail
    if (typeof xiangqing === 'string') {
      cuowu_xinxi = xiangqing
    } else if (Array.isArray(xiangqing)) {
      cuowu_xinxi = xiangqing.map((e) => e.msg || JSON.stringify(e)).join('; ')
    } else if (xiangqing && typeof xiangqing === 'object') {
      cuowu_xinxi = xiangqing.msg || JSON.stringify(xiangqing)
    } else if (cuowu.message) {
      cuowu_xinxi = cuowu.message
    }

    // 401 未授权，清除登录信息并跳转
    if (cuowu.response?.status === 401) {
      localStorage.removeItem('lingpai')
      localStorage.removeItem('yonghu')
      window.location.href = '/login'
    }
    return Promise.reject(new Error(cuowu_xinxi))
  },
)

// ============ 认证相关接口 ============

// 登录
export function denglu(yonghu_ming, mima) {
  return qingqiu_shili.post('/auth/login', { username: yonghu_ming, password: mima })
}

// 获取当前登录用户信息
export function huoquDangqianYonghu() {
  return qingqiu_shili.get('/auth/me')
}

// ============ 道路管理接口 ============

// 获取道路列表
export function huoquDaoluLiebiao(params = {}) {
  return qingqiu_shili.get('/roads', { params })
}

// 新增道路
export function xinzengDaolu(shuju) {
  return qingqiu_shili.post('/roads', shuju)
}

// 编辑道路
export function bianjiDaolu(id, shuju) {
  return qingqiu_shili.put(`/roads/${id}`, shuju)
}

// 删除道路
export function shanchuDaolu(id) {
  return qingqiu_shili.delete(`/roads/${id}`)
}

// ============ 巡检管理接口 ============

// 创建巡检（上传图片进行 AI 分析）
// 注意：不要手动设置 Content-Type，让 axios 自动生成带 boundary 的 multipart/form-data，
// 否则后端无法正确解析上传的文件
export function chuangjianXunjian(biaodan_shuju) {
  return qingqiu_shili.post('/inspections', biaodan_shuju)
}

// 获取巡检列表
export function huoquXunjianLiebiao(params = {}) {
  return qingqiu_shili.get('/inspections', { params })
}

// 获取巡检详情
export function huoquXunjianXiangqing(id) {
  return qingqiu_shili.get(`/inspections/${id}`)
}

// ============ 裂缝分割接口 ============

// 获取分割模型列表与权重状态
export function huoquFengeMoxing() {
  return qingqiu_shili.get('/segmentation/models')
}

// 获取训练/消融实验汇总
export function huoquFengeShiyan() {
  return qingqiu_shili.get('/segmentation/experiments')
}

// 单模型分割分析（save_inspection=true 时保存为巡检记录）
export function fenxiFenge(biaodan_shuju) {
  return qingqiu_shili.post('/segmentation/analyze', biaodan_shuju)
}

// 双模型对比分析
export function duibiFenge(biaodan_shuju) {
  return qingqiu_shili.post('/segmentation/compare', biaodan_shuju)
}

// 预处理对比（none / clahe / full）
export function yuchuliDuibi(biaodan_shuju) {
  return qingqiu_shili.post('/segmentation/preprocess-demo', biaodan_shuju)
}

// ============ 工单管理接口 ============

// 获取工单列表
export function huoquGongdanLiebiao(params = {}) {
  return qingqiu_shili.get('/workorders', { params })
}

// 更新工单状态和处理结果
export function gengxinGongdan(id, shuju) {
  return qingqiu_shili.put(`/workorders/${id}`, shuju)
}

// ============ 仪表盘接口 ============

// 获取仪表盘统计数据
export function huoquYibiaopan() {
  return qingqiu_shili.get('/dashboard')
}

// ============ 用户管理接口 ============

// 获取用户列表
export function huoquYonghuLiebiao() {
  return qingqiu_shili.get('/users')
}

// 新增用户
export function xinzengYonghu(shuju) {
  return qingqiu_shili.post('/users', shuju)
}

// 编辑用户
export function bianjiYonghu(id, shuju) {
  return qingqiu_shili.put(`/users/${id}`, shuju)
}

export default qingqiu_shili
