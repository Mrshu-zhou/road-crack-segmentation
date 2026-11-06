from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import huoqu_shujuku
from models import Inspection, WorkOrder, Road, User
from routers.auth import huoqu_dangqian_yonghu

router = APIRouter(prefix='/api/dashboard', tags=['dashboard'])


@router.get('')
def yilan_huizong(yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """仪表盘统计：巡检总数、缺陷类型分布、严重程度分布、工单状态统计、最近7天趋势"""
    # 巡检总数
    xunjian_zongshu = db.query(func.count(Inspection.id)).scalar() or 0

    # 道路总数
    daolu_zongshu = db.query(func.count(Road.id)).scalar() or 0

    # 工单状态统计
    gongdan_zongshu = db.query(func.count(WorkOrder.id)).scalar() or 0
    dengdai_gongdanshu = db.query(func.count(WorkOrder.id)).filter(WorkOrder.status == 'pending').scalar() or 0
    chulizhong_gongdanshu = db.query(func.count(WorkOrder.id)).filter(WorkOrder.status == 'processing').scalar() or 0
    yiwancheng_gongdanshu = db.query(func.count(WorkOrder.id)).filter(WorkOrder.status == 'completed').scalar() or 0

    # 遍历巡检记录，统计缺陷类型和严重程度分布
    queshi_fenbu = {}
    yansong_fenbu = {}
    xunjian_jilu = db.query(Inspection).all()
    for xj in xunjian_jilu:
        ai = xj.ai_result or {}
        queshi_leixing = ai.get('queshi_leixing', '未知')
        yansong_chengdu = ai.get('yansong_chengdu', '未知')
        queshi_fenbu[queshi_leixing] = queshi_fenbu.get(queshi_leixing, 0) + 1
        yansong_fenbu[yansong_chengdu] = yansong_fenbu.get(yansong_chengdu, 0) + 1

    # 最近7天巡检趋势
    qitian_qian = datetime.now() - timedelta(days=6)
    qushi_jilu = db.query(Inspection).filter(Inspection.created_at >= qitian_qian).all()
    meiri_tongji = {}
    pianyi = 0
    while pianyi <= 6:
        riqi = (datetime.now() - timedelta(days=6 - pianyi)).strftime('%Y-%m-%d')
        meiri_tongji[riqi] = {'date': riqi, 'total': 0, 'defects': 0}
        pianyi += 1
    for xj in qushi_jilu:
        if not xj.created_at:
            continue
        riqi = xj.created_at.strftime('%Y-%m-%d')
        if riqi in meiri_tongji:
            meiri_tongji[riqi]['total'] += 1
            ai = xj.ai_result or {}
            # 缺陷类型不是"无"或"无法识别"的算作有缺陷
            queshi_leixing = ai.get('queshi_leixing', '')
            if queshi_leixing and queshi_leixing not in ('无', '无法识别', 'API 错误', '解析错误'):
                meiri_tongji[riqi]['defects'] += 1

    qushi_liebiao = [meiri_tongji[k] for k in sorted(meiri_tongji.keys())]

    return {
        'total_inspections': xunjian_zongshu,
        'total_roads': daolu_zongshu,
        'total_workorders': gongdan_zongshu,
        'pending_workorders': dengdai_gongdanshu,
        'processing_workorders': chulizhong_gongdanshu,
        'completed_workorders': yiwancheng_gongdanshu,
        'defect_type_distribution': queshi_fenbu,
        'severity_distribution': yansong_fenbu,
        'trend_7days': qushi_liebiao,
    }
