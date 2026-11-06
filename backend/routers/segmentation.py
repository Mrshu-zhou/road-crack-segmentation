# -*- coding: utf-8 -*-
"""裂缝分割相关接口"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import huoqu_shujuku
from models import Inspection, User, WorkOrder
from routers.auth import huoqu_dangqian_yonghu
from routers.inspections import (
    CHUFA_GONGDAN_CHENGDU,
    baocun_shangchuan_tupian,
    goujian_tupian_url,
)
from services import segmentation_service

router = APIRouter(prefix='/api/segmentation', tags=['segmentation'])


@router.get('/models')
def moxing_qingdan(yonghu: User = Depends(huoqu_dangqian_yonghu)):
    """返回可用模型及验证集指标"""
    return {'items': segmentation_service.list_models()}


@router.get('/experiments')
def shiyan_jieguo(yonghu: User = Depends(huoqu_dangqian_yonghu)):
    """返回训练/消融实验汇总，供前端图表展示"""
    return segmentation_service.load_experiments()


@router.post('/preprocess-demo')
def yuchuli_duibi(
    tupian: UploadFile = File(...),
    yonghu: User = Depends(huoqu_dangqian_yonghu),
):
    """上传图片，返回 none / clahe / full 三种预处理结果"""
    tupian_lujing = baocun_shangchuan_tupian(tupian)
    try:
        return segmentation_service.preprocess_demo(tupian_lujing)
    except segmentation_service.SegmentationError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post('/analyze')
def fenxi_tupian(
    tupian: UploadFile = File(...),
    model_key: str = Form('deeplabv3plus_mobilenetv2'),
    mm_per_pixel: float = Form(1.0),
    preprocess: Optional[str] = Form(None),
    road_id: Optional[int] = Form(None),
    save_inspection: bool = Form(False),
    yonghu: User = Depends(huoqu_dangqian_yonghu),
    db: Session = Depends(huoqu_shujuku),
):
    """单模型分割分析；save_inspection=true 时写入巡检记录并自动生成工单"""
    tupian_lujing = baocun_shangchuan_tupian(tupian)
    try:
        jieguo = segmentation_service.analyze_image(
            tupian_lujing, model_key,
            mm_per_pixel=mm_per_pixel,
            preprocess_override=preprocess,
        )
    except segmentation_service.SegmentationError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if not save_inspection:
        return {
            'image_url': goujian_tupian_url(tupian_lujing),
            'result': jieguo,
            'auto_workorder': False,
        }

    ai_jieguo = {
        'fenxi_fangshi': 'segmentation',
        'model_key': jieguo['model_key'],
        'model_label': jieguo['model_label'],
        'queshi_leixing': jieguo['queshi_leixing'],
        'yansong_chengdu': jieguo['yansong_chengdu'],
        'yansong_laizhi': 'guize',
        'yansong_yiju': jieguo['yansong_yiju'],
        'queshi_weizhi': jieguo['queshi_weizhi'],
        'daolu_zhuangkuang': jieguo['daolu_zhuangkuang'],
        'chuli_jianyi': jieguo['chuli_jianyi'],
        'suo_xu_cailiao': '密封胶、沥青修补料',
        'yingji_chengdu': jieguo['yingji_chengdu'],
        'seg': {
            'mask_url': jieguo['mask_url'],
            'overlay_url': jieguo['overlay_url'],
            'latency_ms': jieguo['latency_ms'],
            'preprocess_mode': jieguo['preprocess_mode'],
            'quantification': jieguo['quantification'],
        },
    }

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

    zidong_gongdan = False
    yingji_chengdu = jieguo.get('yingji_chengdu', '')
    if yingji_chengdu in CHUFA_GONGDAN_CHENGDU:
        gongdan = WorkOrder(
            inspection_id=xunjian.id,
            road_id=road_id,
            queshi_leixing=jieguo['queshi_leixing'],
            yansong_chengdu=jieguo['yansong_chengdu'],
            chuli_jianyi=jieguo['chuli_jianyi'],
            status='pending',
        )
        db.add(gongdan)
        db.commit()
        zidong_gongdan = True

    return {
        'id': xunjian.id,
        'image_url': goujian_tupian_url(tupian_lujing),
        'ai_result': ai_jieguo,
        'auto_workorder': zidong_gongdan,
        'message': '分割巡检完成',
    }


@router.post('/compare')
def duibi_fenxi(
    tupian: UploadFile = File(...),
    mm_per_pixel: float = Form(1.0),
    preprocess: Optional[str] = Form(None),
    yonghu: User = Depends(huoqu_dangqian_yonghu),
):
    """双模型对比分析"""
    tupian_lujing = baocun_shangchuan_tupian(tupian)
    results = segmentation_service.compare_models(
        tupian_lujing, mm_per_pixel=mm_per_pixel, preprocess_override=preprocess
    )
    return {
        'image_url': goujian_tupian_url(tupian_lujing),
        'results': results,
    }
