import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElIcons from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './style.css'

// 创建 Vue 应用实例
const app = createApp(App)

// 注册 Element Plus 所有图标为全局组件
for (const [tubiao_mingcheng, tubiao_zujian] of Object.entries(ElIcons)) {
  app.component(tubiao_mingcheng, tubiao_zujian)
}

// 注册 Pinia 状态管理和路由
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { size: 'default' })

app.mount('#app')
