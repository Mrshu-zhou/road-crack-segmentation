import os
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import huoqu_shujuku
from models import Inspection, WorkOrder, Road, User
from services.ai_service import fenxi_daolu_tupian
from services.dingji import panduan_yanzhong, DINGJI_SHUNXU
from routers.auth import huoqu_dangqian_yonghu
from config import SHANGCHUAN_MULU, YUNXU_TUPIAN_KUOZHANMING, ZUIDA_TUPIAN_DAXIAO

rizhi = logging.getLogger(__name__)
router = APIRouter(prefix='/api/inspections', tags=['inspections'])

# 触发自动创建工单的紧急程度
CHUFA_GONGDAN_CHENGDU = {'建议绕行', '立即封路'}


def yansong_guizehua(ai_jieguo):
    """对 AI 分析结果执行严重程度规则化。

    遍历缺陷清单中的每个缺陷，用规则引擎逐项定级并取最严重者；
    规则得出结果时覆盖模型直接输出的严重程度，并记录判定来源与依据。
    若无任何量化信息可判，则保持模型结果（来源记为 moxing）。
    """
    qingdan = ai_jieguo.get('quexian_qingdan') or []
    zui_yan = '无'
    zui_yiju = ''
    you_guize = False

    for tiao in qingdan:
        leixing = tiao.get('leixing', '')
        dengji, laizhi, yiju = panduan_yanzhong(
            leixing, tiao.get('chicun_gu_ji', ''), tiao.get('jiankuang'), None
        )
        if DINGJI_SHUNXU.get(dengji, 0) > DINGJI_SHUNXU.get(zui_yan, 0):
            zui_yan = dengji
            zui_yiju = yiju
        if laizhi == 'guize':
            you_guize = True

    # 无缺陷清单时，用整图主要缺陷字段判定（通常无尺寸/框，走模型兜底）
    if not qingdan:
        dengji, laizhi, yiju = panduan_yanzhong(
            ai_jieguo.get('queshi_leixing', ''), '', None,
            ai_jieguo.get('yansong_chengdu', ''),
        )
        if laizhi == 'guize':
            zui_yan = dengji
            zui_yiju = yiju
            you_guize = True

    if you_guize:
        # 规则判定的等级不把"有缺陷"误判为"无"
        if zui_yan != '无':
            ai_jieguo['yansong_chengdu'] = zui_yan
        ai_jieguo['yansong_laizhi'] = 'guize'
        ai_jieguo['yansong_yiju'] = zui_yiju or '按缺陷尺寸/面积阈值分级'
    else:
        ai_jieguo['yansong_laizhi'] = 'moxing'
        ai_jieguo.pop('yansong_yiju', None)


def baocun_shangchuan_tupian(wenjian: UploadFile) -> str:
    """保存上传的图片到 uploads 目录，返回完整文件路径"""
    kuozhanming = os.path.splitext(wenjian.filename or '.jpg')[1].lower()
    if kuozhanming not in YUNXU_TUPIAN_KUOZHANMING:
        raise HTTPException(status_code=400, detail=f'不支持的图片格式: {kuozhanming}')
    # 检查文件大小
    wenjian.file.seek(0, 2)
    daxiao = wenjian.file.tell()
    wenjian.file.seek(0)
    if daxiao > ZUIDA_TUPIAN_DAXIAO:
        raise HTTPException(status_code=400, detail='图片大小不能超过10MB')
    # 用 uuid 命名
    wenjianming = f'{uuid.uuid4().hex}{kuozhanming}'
    wenjianlujing = os.path.join(SHANGCHUAN_MULU, wenjianming)
    with open(wenjianlujing, 'wb') as f:
        f.write(wenjian.file.read())
    return wenjianlujing


def goujian_tupian_url(tupian_lujing: str) -> str:
    """根据图片完整路径构造访问 URL"""
    if not tupian_lujing:
        return ''
    wenjianming = os.path.basename(tupian_lujing)
    return f'/uploads/{wenjianming}'


@router.post('')
def chuangjian_xunjian(
    tupian: UploadFile = File(...),
    road_id: Optional[int] = Form(None),
    yonghu: User = Depends(huoqu_dangqian_yonghu),
    db: Session = Depends(huoqu_shujuku),
):
    """上传图片→调用AI分析→创建巡检记录→紧急程度为建议绕行或立即封路时自动创建工单"""
    # 1. 保存图片
    tupian_lujing = baocun_shangchuan_tupian(tupian)

    # 2. 调用 AI 分析
    ai_jieguo = fenxi_daolu_tupian(tupian_lujing)

    # 2.5 严重程度规则化修正（规则引擎优先，模型输出兜底）
    yansong_guizehua(ai_jieguo)

    # 3. 创建巡检记录
    xunjian = Inspection(
        road_id=road_id,
        inspector_id=yonghu.id,
        image_path=tupian_lujing,
        ai_result=ai_jieguo,
        status='completed',
    )
    db.add(xunjian)
    db.commit()
    db.refresh(xunjian)

    # 4. 紧急程度为"建议绕行"或"立即封路"时自动创建工单
    zidong_gongdan = False
    yingji_chengdu = ai_jieguo.get('yingji_chengdu', '')
    if yingji_chengdu in CHUFA_GONGDAN_CHENGDU:
        gongdan = WorkOrder(
            inspection_id=xunjian.id,
            road_id=road_id,
            queshi_leixing=ai_jieguo.get('queshi_leixing', ''),
            yansong_chengdu=ai_jieguo.get('yansong_chengdu', ''),
            chuli_jianyi=ai_jieguo.get('chuli_jianyi', ''),
            status='pending',
        )
        db.add(gongdan)
        db.commit()
        zidong_gongdan = True

    return {
        'id': xunjian.id,
        'road_id': xunjian.road_id,
        'image_url': goujian_tupian_url(tupian_lujing),
        'ai_result': ai_jieguo,
        'auto_workorder': zidong_gongdan,
        'message': '巡检完成',
    }


@router.get('')
def xunjian_liebiao(
    road_id: Optional[int] = None,
    queshi_leixing: Optional[str] = None,
    yansong_chengdu: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    yonghu: User = Depends(huoqu_dangqian_yonghu),
    db: Session = Depends(huoqu_shujuku),
):
    """巡检列表，支持 road_id、缺陷类型、严重程度筛选和分页"""
    chaxun = db.query(Inspection)
    if road_id:
        chaxun = chaxun.filter(Inspection.road_id == road_id)

    xunjianjilu = chaxun.order_by(Inspection.created_at.desc()).all()

    jieguo = []
    for xj in xunjianjilu:
        ai = xj.ai_result or {}
        # 在 Python 层过滤 ai_result 中的字段
        if queshi_leixing and ai.get('queshi_leixing') != queshi_leixing:
            continue
        if yansong_chengdu and ai.get('yansong_chengdu') != yansong_chengdu:
            continue

        # 关联道路信息
        daolu_mingcheng = ''
        daolu_duanming = ''
        if xj.road:
            daolu_mingcheng = xj.road.road_name
            daolu_duanming = xj.road.section

        jieguo.append({
            'id': xj.id,
            'road_id': xj.road_id,
            'road_name': daolu_mingcheng,
            'section': daolu_duanming,
            'inspector_name': xj.inspector.real_name or xj.inspector.username if xj.inspector else '',
            'image_url': goujian_tupian_url(xj.image_path),
            'ai_result': ai,
            'status': xj.status,
            'created_at': xj.created_at.isoformat() if xj.created_at else '',
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


@router.get('/{inspection_id}')
def huoqu_xunjian_xiangqing(inspection_id: int, yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """获取巡检详情，包含关联工单"""
    xj = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not xj:
        raise HTTPException(status_code=404, detail='巡检记录不存在')

    # 关联工单列表
    gongdanliebiao = []
    for gd in xj.workorders:
        gongdanliebiao.append({
            'id': gd.id,
            'queshi_leixing': gd.queshi_leixing,
            'yansong_chengdu': gd.yansong_chengdu,
            'status': gd.status,
            'result_note': gd.result_note,
            'created_at': gd.created_at.isoformat() if gd.created_at else '',
            'completed_at': gd.completed_at.isoformat() if gd.completed_at else None,
        })

    daolu_mingcheng = ''
    daolu_duanming = ''
    daolu_leixing = ''
    if xj.road:
        daolu_mingcheng = xj.road.road_name
        daolu_duanming = xj.road.section
        daolu_leixing = xj.road.road_type

    return {
        'id': xj.id,
        'road_id': xj.road_id,
        'road_name': daolu_mingcheng,
        'section': daolu_duanming,
        'road_type': daolu_leixing,
        'inspector_name': xj.inspector.real_name or xj.inspector.username if xj.inspector else '',
        'image_url': goujian_tupian_url(xj.image_path),
        'ai_result': xj.ai_result,
        'status': xj.status,
        'workorders': gongdanliebiao,
        'created_at': xj.created_at.isoformat() if xj.created_at else '',
    }
