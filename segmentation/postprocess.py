# -*- coding: utf-8 -*-
"""分割掩码后处理"""

import numpy as np
from skimage.morphology import closing, disk, remove_small_objects


def postprocess_mask(probability, threshold=0.5, min_area=30, close_radius=1):
    """概率图 -> 二值掩码：阈值 + 去除小连通域 + 形态学闭运算"""
    mask = np.asarray(probability) >= threshold
    mask = remove_small_objects(mask, max_size=max(0, min_area - 1), connectivity=2)
    if close_radius > 0:
        mask = closing(mask, disk(close_radius))
    return mask
