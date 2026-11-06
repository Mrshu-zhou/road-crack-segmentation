# -*- coding: utf-8 -*-
"""
分割模型推理服务。

职责：
  1. 懒加载两个分割模型权重；
  2. 复用 segmentation/preprocessing.py 的预处理；
  3. 输出掩码、叠加图、量化指标与严重程度；
  4. 为前端提供模型清单与实验结果摘要。
"""

import json
import sys
import time
import uuid
from pathlib import Path

import cv2
import numpy as np
import torch

# segmentation 模块与 backend 存在同名文件（config/models），已重命名为 seg_config/seg_models
SEG_ROOT = Path(__file__).resolve().parents[2] / 'segmentation'
if str(SEG_ROOT) not in sys.path:
    sys.path.insert(0, str(SEG_ROOT))

from config import SHANGCHUAN_MULU  # backend/config.py
from postprocess import postprocess_mask
from preprocessing import analyze_image_stats, apply_preprocess, normalize_image
from quantification import quantify_mask
from seg_config import MODEL_LABELS
from seg_models import build_model

MODEL_KEYS = tuple(MODEL_LABELS.keys())
SEG_UPLOAD_DIR = Path(SHANGCHUAN_MULU) / 'segmentation'
SEG_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_MODEL_CACHE = {}
_DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

YINGJI_MAP = {
    '严重': '立即封路',
    '中等': '建议绕行',
    '轻微': '低速行驶通过',
    '无': '无需处理',
}

CHULI_JIANYI_MAP = {
    '严重': '建议立即封闭该路段，安排灌缝与基层补强处理，防止雨水渗入扩大病害。',
    '中等': '建议 7 天内安排密封胶灌缝处理，并提高该路段巡查频次。',
    '轻微': '建议记录并持续观察，下次巡检复查裂缝扩展情况。',
    '无': '当前未检出明显裂缝，保持常规巡检。',
}


class SegmentationError(RuntimeError):
    """分割服务异常"""


def _weights_path(model_key):
    return SEG_ROOT / 'weights' / f'{model_key}_best.pth'


def _load_model(model_key):
    """懒加载并缓存模型"""
    if model_key not in MODEL_LABELS:
        raise SegmentationError(f'未知模型: {model_key}')
    if model_key in _MODEL_CACHE:
        return _MODEL_CACHE[model_key]

    weights = _weights_path(model_key)
    if not weights.exists():
        raise SegmentationError(f'模型权重不存在: {weights}，请先完成训练')

    checkpoint = torch.load(weights, map_location=_DEVICE, weights_only=False)
    model = build_model(model_key, encoder_weights=None, classes=1)
    model.load_state_dict(checkpoint['state_dict'])
    model.to(_DEVICE)
    model.eval()
    _MODEL_CACHE[model_key] = (model, checkpoint)
    return model, checkpoint


def _prepare_input(image_bgr, max_side=1024):
    """缩放超大图并填充到 32 的倍数，返回张量与缩放信息"""
    original_h, original_w = image_bgr.shape[:2]
    scale = min(1.0, max_side / max(original_h, original_w))
    if scale < 1.0:
        resized_h = max(32, int(round(original_h * scale)))
        resized_w = max(32, int(round(original_w * scale)))
        image_bgr = cv2.resize(image_bgr, (resized_w, resized_h), interpolation=cv2.INTER_AREA)
    else:
        resized_h, resized_w = original_h, original_w

    target_h = int(np.ceil(resized_h / 32) * 32)
    target_w = int(np.ceil(resized_w / 32) * 32)
    pad_h = target_h - resized_h
    pad_w = target_w - resized_w
    if pad_h or pad_w:
        image_bgr = cv2.copyMakeBorder(
            image_bgr, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT_101
        )

    return image_bgr, (original_h, original_w), (resized_h, resized_w)


def _predict_probability(image_bgr, model, preprocess_mode):
    """单张图前向推理，返回原图尺寸的概率图"""
    prepared, original_size, resized_size = _prepare_input(image_bgr)
    image_rgb = apply_preprocess(prepared, preprocess_mode)
    tensor = torch.from_numpy(normalize_image(image_rgb)).unsqueeze(0).to(_DEVICE)

    if _DEVICE.type == 'cuda':
        torch.cuda.synchronize()
    start = time.time()
    with torch.no_grad():
        logits = model(tensor)
        probability = torch.sigmoid(logits)[0, 0].cpu().numpy()
    if _DEVICE.type == 'cuda':
        torch.cuda.synchronize()
    latency_ms = (time.time() - start) * 1000.0

    resized_h, resized_w = resized_size
    probability = probability[:resized_h, :resized_w]
    original_h, original_w = original_size
    if (resized_h, resized_w) != (original_h, original_w):
        probability = cv2.resize(probability, (original_w, original_h), interpolation=cv2.INTER_LINEAR)
    return probability, latency_ms


def _save_visuals(image_bgr, mask, uid):
    """保存掩码图与叠加图，返回访问 URL"""
    mask_image = (mask.astype(np.uint8) * 255)
    mask_name = f'{uid}_mask.png'
    overlay_name = f'{uid}_overlay.jpg'

    cv2.imwrite(str(SEG_UPLOAD_DIR / mask_name), mask_image)

    overlay = image_bgr.copy()
    layer = np.zeros_like(overlay)
    layer[mask] = (0, 0, 255)
    overlay = cv2.addWeighted(overlay, 0.65, layer, 0.35, 0)
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (0, 0, 255), 2)
    cv2.imwrite(str(SEG_UPLOAD_DIR / overlay_name), overlay)

    return f'/uploads/segmentation/{mask_name}', f'/uploads/segmentation/{overlay_name}'


def _grade_and_text(quantification):
    grade = quantification.get('grade', '无')
    return {
        'yansong_chengdu': grade,
        'yingji_chengdu': YINGJI_MAP.get(grade, '无需处理'),
        'chuli_jianyi': CHULI_JIANYI_MAP.get(grade, CHULI_JIANYI_MAP['无']),
    }


def analyze_image(image_path, model_key, mm_per_pixel=1.0, preprocess_override=None):
    """单模型分割 + 量化 + 分级"""
    image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise SegmentationError(f'图片读取失败: {image_path}')

    model, checkpoint = _load_model(model_key)
    preprocess_mode = preprocess_override or checkpoint.get('preprocess_mode', 'full')
    probability, latency_ms = _predict_probability(image_bgr, model, preprocess_mode)
    mask = postprocess_mask(probability, threshold=0.5)
    quantification = quantify_mask(mask, mm_per_pixel=mm_per_pixel)
    text = _grade_and_text(quantification)

    uid = uuid.uuid4().hex
    mask_url, overlay_url = _save_visuals(image_bgr, mask, uid)

    defect_count = quantification.get('defect_count', 0)
    zhuangkuang = (
        f'检出 {defect_count} 处裂缝，累计长度 {quantification["length_mm"]:.1f} 毫米，'
        f'最大宽度 {quantification["width_max_mm"]:.1f} 毫米'
        if defect_count else '未检出明显裂缝'
    )

    return {
        'model_key': model_key,
        'model_label': MODEL_LABELS.get(model_key, model_key),
        'preprocess_mode': preprocess_mode,
        'latency_ms': round(latency_ms, 2),
        'mask_url': mask_url,
        'overlay_url': overlay_url,
        'daolu_zhuangkuang': zhuangkuang,
        'queshi_leixing': '裂缝' if defect_count else '无',
        'queshi_weizhi': '路面图像区域',
        'yansong_laizhi': 'guize',
        'yansong_yiju': quantification.get('grade_reason', ''),
        'quantification': quantification,
        **text,
    }


def compare_models(image_path, mm_per_pixel=1.0, preprocess_override=None):
    """双模型对比推理"""
    results = []
    for model_key in MODEL_KEYS:
        try:
            results.append(analyze_image(
                image_path, model_key,
                mm_per_pixel=mm_per_pixel,
                preprocess_override=preprocess_override,
            ))
        except SegmentationError as error:
            results.append({'model_key': model_key, 'error': str(error)})
    return results


def preprocess_demo(image_path):
    """保存 none / clahe / full 三种预处理结果，供前端对照"""
    image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise SegmentationError(f'图片读取失败: {image_path}')

    uid = uuid.uuid4().hex
    urls = {}
    for mode in ('none', 'clahe', 'full'):
        image_rgb = apply_preprocess(image_bgr, mode)
        filename = f'{uid}_{mode}.jpg'
        cv2.imwrite(str(SEG_UPLOAD_DIR / filename), cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
        urls[mode] = f'/uploads/segmentation/{filename}'

    return {
        'urls': urls,
        'stats': {
            'none': analyze_image_stats(image_bgr),
            'clahe': analyze_image_stats(cv2.cvtColor(apply_preprocess(image_bgr, 'clahe'), cv2.COLOR_RGB2BGR)),
            'full': analyze_image_stats(cv2.cvtColor(apply_preprocess(image_bgr, 'full'), cv2.COLOR_RGB2BGR)),
        },
    }


def list_models():
    """返回模型可用状态与验证集指标"""
    items = []
    for model_key, label in MODEL_LABELS.items():
        weights = _weights_path(model_key)
        item = {
            'model_key': model_key,
            'label': label,
            'available': weights.exists(),
            'weights_path': str(weights),
        }
        if weights.exists():
            try:
                checkpoint = torch.load(weights, map_location='cpu', weights_only=False)
                item['preprocess_mode'] = checkpoint.get('preprocess_mode', '')
                item['val_metrics'] = checkpoint.get('val_metrics', {})
                item['best_epoch'] = checkpoint.get('epoch')
            except Exception as error:  # 权重损坏时仍返回列表，避免前端整页失败
                item['error'] = str(error)
        items.append(item)
    return items


def load_experiments():
    """读取实验汇总 JSON，供前端画图"""
    summary_path = SEG_ROOT / 'runs' / 'experiments_summary.json'
    if not summary_path.exists():
        return {'summary': [], 'evaluations': [], 'ablation': {}}
    with open(summary_path, 'r', encoding='utf-8') as f:
        return json.load(f)
