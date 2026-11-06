# -*- coding: utf-8 -*-
"""
裂缝量化与严重程度分级。

量化指标：
  - 连通域数量
  - 骨架长度（像素/毫米）
  - 距离变换估算裂缝宽度（像素/毫米）
  - 裂缝面积与图像面积占比

分级规则复用 backend/services/dingji.py 中 JTG 5210 的裂缝宽度阈值。
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt
from skimage.morphology import remove_small_objects, skeletonize

# 复用现有后端规则引擎（backend/services/dingji.py）
_BACKEND_SERVICES = Path(__file__).resolve().parents[1] / 'backend' / 'services'
if str(_BACKEND_SERVICES) not in sys.path:
    sys.path.insert(0, str(_BACKEND_SERVICES))

from dingji import panduan_yanzhong  # noqa: E402

MIN_COMPONENT_AREA = 30


def _component_quantification(component, mm_per_pixel):
    """单个连通域的骨架长度与宽度估计"""
    skeleton = skeletonize(component)
    if skeleton.sum() == 0:
        return {'length_px': 0.0, 'width_mean_px': 0.0, 'width_max_px': 0.0}

    distance = distance_transform_edt(component)
    widths = 2.0 * distance[skeleton]
    return {
        'length_px': float(skeleton.sum()),
        'width_mean_px': float(np.mean(widths)),
        'width_max_px': float(np.percentile(widths, 95)),
    }


def quantify_mask(mask, mm_per_pixel=1.0):
    """
    对二值裂缝掩码做量化并给出严重程度。

    参数:
        mask: bool 或 0/1 掩码
        mm_per_pixel: 物理标定比例，默认 1 像素 = 1 毫米
    """
    mask = np.asarray(mask).astype(np.uint8)
    height, width = mask.shape[:2]
    mm_per_pixel = float(mm_per_pixel) if mm_per_pixel else 1.0
    if mm_per_pixel <= 0:
        mm_per_pixel = 1.0

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    components = []
    total_area = 0
    total_length = 0.0
    widths = []
    for label_id in range(1, num_labels):
        area = int(stats[label_id, cv2.CC_STAT_AREA])
        if area < MIN_COMPONENT_AREA:
            continue
        component = labels == label_id
        item = _component_quantification(component, mm_per_pixel)
        item.update({
            'area_px': area,
            'bbox': [
                int(stats[label_id, cv2.CC_STAT_LEFT]),
                int(stats[label_id, cv2.CC_STAT_TOP]),
                int(stats[label_id, cv2.CC_STAT_WIDTH]),
                int(stats[label_id, cv2.CC_STAT_HEIGHT]),
            ],
        })
        components.append(item)
        total_area += area
        total_length += item['length_px']
        widths.append(item['width_max_px'])

    area_ratio = total_area / float(height * width) if height * width else 0.0
    width_max_px = float(max(widths)) if widths else 0.0
    width_mean_px = float(np.mean(widths)) if widths else 0.0

    width_max_mm = width_max_px * mm_per_pixel
    width_mean_mm = width_mean_px * mm_per_pixel
    length_mm = total_length * mm_per_pixel
    area_mm2 = total_area * (mm_per_pixel ** 2)

    # 严重程度：优先按裂缝宽度分级，宽度不可用时按面积占比
    if width_max_mm > 0:
        grade, grade_source, grade_reason = panduan_yanzhong(
            '裂缝', f'宽度约{width_max_mm:.1f}毫米', None, None
        )
    else:
        side = float(np.sqrt(area_ratio))
        grade, grade_source, grade_reason = panduan_yanzhong(
            '裂缝', '', [0.0, 0.0, side, side], None
        )

    components.sort(key=lambda item: item['area_px'], reverse=True)
    return {
        'defect_count': len(components),
        'area_px': total_area,
        'area_ratio': float(area_ratio),
        'area_mm2': float(area_mm2),
        'length_px': float(total_length),
        'length_mm': float(length_mm),
        'width_mean_px': width_mean_px,
        'width_max_px': width_max_px,
        'width_mean_mm': float(width_mean_mm),
        'width_max_mm': float(width_max_mm),
        'mm_per_pixel': mm_per_pixel,
        'grade': grade,
        'grade_source': grade_source,
        'grade_reason': grade_reason,
        'components': components[:10],
    }
