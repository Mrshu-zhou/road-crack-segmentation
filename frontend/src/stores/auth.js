import { defineStore } from 'pinia'
import { denglu as dengluApi, huoquDangqianYonghu } from '../api'

// 认证状态管理
export const useAuthStore = defineStore('auth', {
  state: () => ({
    // 登录令牌
    lingpai: localStorage.getItem('lingpai') || '',
    // 当前用户信息（包含 role 角色）
    yonghu: JSON.parse(localStorage.getItem('yonghu') || 'null'),
  }),

  getters: {
    // 是否已登录
    yiDenglu: (state) => !!state.lingpai,
    // 当前用户角色
    juese: (state) => state.yonghu?.role || '',
    // 当前用户名
    yonghuMing: (state) => state.yonghu?.username || '',
  },

  actions: {
    // 登录方法
    async denglu(yonghu_ming, mima) {
      const shuju = await dengluApi(yonghu_ming, mima)
      this.lingpai = shuju.access_token
      this.yonghu = shuju.user
      localStorage.setItem('lingpai', this.lingpai)
      localStorage.setItem('yonghu', JSON.stringify(this.yonghu))
      return shuju
    },

    // 登出方法
    dengchu() {
      this.lingpai = ''
      this.yonghu = null
      localStorage.removeItem('lingpai')
      localStorage.removeItem('yonghu')
    },

    // 刷新当前用户信息
    async shuaxinYonghu() {
      if (!this.lingpai) return
      try {
        const yonghu = await huoquDangqianYonghu()
        this.yonghu = yonghu
        localStorage.setItem('yonghu', JSON.stringify(yonghu))
      } catch (e) {
        // 获取失败则登出
        this.dengchu()
      }
    },
  },
})
