# -*- coding: utf-8 -*-
"""
道路无人机巡检缺陷检测系统 - FastAPI 入口
"""

import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import SHANGCHUAN_MULU
from database import chushihua_shujuku
from routers import auth, roads, inspections, workorders, dashboard, users, segmentation

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
rizhi = logging.getLogger(__name__)

yingyong = FastAPI(title='道路无人机巡检缺陷检测系统', version='1.0.0')

# 跨域配置
yingyong.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 确保上传目录存在
os.makedirs(SHANGCHUAN_MULU, exist_ok=True)
try:
    yingyong.mount('/uploads', StaticFiles(directory=SHANGCHUAN_MULU), name='uploads')
except Exception:
    rizhi.warning('上传目录无法挂载为静态资源')

# 注册路由
yingyong.include_router(auth.router)
yingyong.include_router(roads.router)
yingyong.include_router(inspections.router)
yingyong.include_router(workorders.router)
yingyong.include_router(dashboard.router)
yingyong.include_router(users.router)
yingyong.include_router(segmentation.router)


@yingyong.on_event('startup')
def qidong():
    """启动时初始化数据库并注入种子数据"""
    chushihua_shujuku()
    import seed
    seed.buzhong_shuju()
    rizhi.info('数据库已初始化并注入种子数据')


@yingyong.get('/api/health')
def jiankang_jiance():
    """健康检查接口"""
    return {'status': 'ok', 'service': '道路无人机巡检缺陷检测系统'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:yingyong', host='0.0.0.0', port=8001, reload=True)
