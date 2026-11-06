from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import huoqu_shujuku
from models import Road, User
from routers.auth import huoqu_dangqian_yonghu

router = APIRouter(prefix='/api/roads', tags=['roads'])


class DaoluChuangjian(BaseModel):
    """道路创建/编辑请求体"""
    road_name: str
    section: str = ''
    road_type: str = '主干道'
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    inspector_id: Optional[int] = None


@router.get('')
def daolu_liebiao(yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """获取所有道路点位列表"""
    daolu_jilu = db.query(Road).order_by(Road.id.asc()).all()
    return {
        'roads': [
            {
                'id': d.id,
                'road_name': d.road_name,
                'section': d.section,
                'road_type': d.road_type,
                'latitude': d.latitude,
                'longitude': d.longitude,
                'inspector_id': d.inspector_id,
                'inspector_name': d.inspector_rel.real_name or d.inspector_rel.username if d.inspector_rel else '',
                'created_at': d.created_at.isoformat() if d.created_at else '',
            }
            for d in daolu_jilu
        ]
    }


@router.post('')
def chuangjian_daolu(shuju: DaoluChuangjian, yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """新建道路点位（仅管理员）"""
    if yonghu.role != 'admin':
        raise HTTPException(status_code=403, detail='仅管理员可创建道路')
    daolu = Road(
        road_name=shuju.road_name,
        section=shuju.section,
        road_type=shuju.road_type,
        latitude=shuju.latitude,
        longitude=shuju.longitude,
        inspector_id=shuju.inspector_id,
    )
    db.add(daolu)
    db.commit()
    db.refresh(daolu)
    return {'id': daolu.id, 'message': '道路创建成功'}


@router.put('/{road_id}')
def gengxin_daolu(road_id: int, shuju: dict, yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """编辑道路点位（仅管理员）"""
    if yonghu.role != 'admin':
        raise HTTPException(status_code=403, detail='仅管理员可编辑道路')
    daolu = db.query(Road).filter(Road.id == road_id).first()
    if not daolu:
        raise HTTPException(status_code=404, detail='道路不存在')
    for jian in ('road_name', 'section', 'road_type', 'latitude', 'longitude', 'inspector_id'):
        if jian in shuju and shuju[jian] is not None:
            setattr(daolu, jian, shuju[jian])
    db.commit()
    return {'message': '道路更新成功'}


@router.delete('/{road_id}')
def shanchu_daolu(road_id: int, yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """删除道路点位（仅管理员）"""
    if yonghu.role != 'admin':
        raise HTTPException(status_code=403, detail='仅管理员可删除道路')
    daolu = db.query(Road).filter(Road.id == road_id).first()
    if not daolu:
        raise HTTPException(status_code=404, detail='道路不存在')
    db.delete(daolu)
    db.commit()
    return {'message': '道路删除成功'}
