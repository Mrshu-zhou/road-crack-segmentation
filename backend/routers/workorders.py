from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import huoqu_shujuku
from models import WorkOrder, Inspection, User
from routers.auth import huoqu_dangqian_yonghu

router = APIRouter(prefix='/api/workorders', tags=['workorders'])


@router.get('')
def gongdan_liebiao(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    yonghu: User = Depends(huoqu_dangqian_yonghu),
    db: Session = Depends(huoqu_shujuku),
):
    """工单列表，支持状态筛选和分页"""
    chaxun = db.query(WorkOrder)
    if status:
        chaxun = chaxun.filter(WorkOrder.status == status)

    gongdan_jilu = chaxun.order_by(WorkOrder.created_at.desc()).all()

    jieguo = []
    for gd in gongdan_jilu:
        xj = gd.inspection
        daolu_mingcheng = ''
        if gd.road:
            daolu_mingcheng = gd.road.road_name
        elif xj and xj.road:
            daolu_mingcheng = xj.road.road_name

        jieguo.append({
            'id': gd.id,
            'inspection_id': gd.inspection_id,
            'road_id': gd.road_id,
            'road_name': daolu_mingcheng,
            'queshi_leixing': gd.queshi_leixing,
            'yansong_chengdu': gd.yansong_chengdu,
            'chuli_jianyi': gd.chuli_jianyi,
            'status': gd.status,
            'result_note': gd.result_note,
            'created_at': gd.created_at.isoformat() if gd.created_at else '',
            'completed_at': gd.completed_at.isoformat() if gd.completed_at else None,
        })

    zongshu = len(jieguo)
    kaishi = (page - 1) * page_size
    jieshu = kaishi + page_size
    return {
        'total': zongshu,
        'page': page,
        'page_size': page_size,
        'items': jieguo[kaishi:jieshu],
    }


@router.put('/{workorder_id}')
def gengxin_gongdan(workorder_id: int, shuju: dict, yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """更新工单状态和结果，completed 时记录 completed_at"""
    gd = db.query(WorkOrder).filter(WorkOrder.id == workorder_id).first()
    if not gd:
        raise HTTPException(status_code=404, detail='工单不存在')

    xin_zhuangtai = shuju.get('status')
    if xin_zhuangtai and xin_zhuangtai not in ('pending', 'processing', 'completed'):
        raise HTTPException(status_code=400, detail='无效工单状态，可选: pending/processing/completed')

    if xin_zhuangtai:
        gd.status = xin_zhuangtai
        # 完成时记录完成时间
        if xin_zhuangtai == 'completed':
            gd.completed_at = datetime.now()

    # 更新结果备注
    if 'result_note' in shuju and shuju['result_note'] is not None:
        gd.result_note = shuju['result_note']

    db.commit()
    return {'message': '工单更新成功'}
