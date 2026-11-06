# -*- coding: utf-8 -*-
"""
图像预处理与增强。

三种模式：
  none  : 仅 RGB 转换，作为基线
  clahe : LAB 空间 CLAHE 对比度增强 + 双边滤波去噪
  full  : clahe + Retinex 去阴影/光照不均 + 轻微反锐化

训练、评估与后端推理必须使用同一模式，模式记录在权重文件中。
"""

import cv2
import numpy as np
from skimage.measure import shannon_entropy

from seg_config import IMAGE_MEAN, IMAGE_STD


def _single_scale_retinex(channel, sigma=30):
    """单尺度 Retinex：抑制光照不均与阴影"""
    x = channel.astype(np.float32) + 1.0
    blurred = cv2.GaussianBlur(x, (0, 0), sigma)
    retinex = np.log10(x) - np.log10(blurred + 1.0)
    retinex = cv2.normalize(retinex, None, 0, 255, cv2.NORM_MINMAX)
    return retinex.astype(np.uint8)


def apply_preprocess(image_bgr, mode='full'):
    """输入 BGR 图像，输出增强后的 RGB 图像"""
    image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    if mode == 'none':
        return image

    if mode not in ('clahe', 'full'):
        raise ValueError(f'未知预处理模式: {mode}')

    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    image = cv2.cvtColor(cv2.merge([l_channel, a_channel, b_channel]), cv2.COLOR_LAB2RGB)
    image = cv2.bilateralFilter(image, 5, 50, 50)

    if mode == 'clahe':
        return image

    # full：在 L 通道做 Retinex，再叠加轻微反锐化
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    l_channel = _single_scale_retinex(l_channel, sigma=30)
    image = cv2.cvtColor(cv2.merge([l_channel, a_channel, b_channel]), cv2.COLOR_LAB2RGB)

    blurred = cv2.GaussianBlur(image, (0, 0), 1.0)
    image = cv2.addWeighted(image, 1.2, blurred, -0.2, 0)
    return np.clip(image, 0, 255).astype(np.uint8)


def normalize_image(image_rgb):
    """RGB uint8 -> ImageNet 归一化后的 CHW float32"""
    image = image_rgb.astype(np.float32) / 255.0
    image = (image - np.array(IMAGE_MEAN, dtype=np.float32)) / np.array(IMAGE_STD, dtype=np.float32)
    return np.transpose(image, (2, 0, 1))


def pad_to_size(image_rgb, mask=None, height=384, width=544):
    """反射填充到指定尺寸（并保证是 32 的倍数），返回填充后的图像、掩码与原始有效区域"""
    original_h, original_w = image_rgb.shape[:2]
    # SegFormer 要求输入尺寸为 32 的倍数；对更大的图也向上取整
    height = max(height, int(np.ceil(original_h / 32) * 32))
    width = max(width, int(np.ceil(original_w / 32) * 32))
    pad_h = max(0, height - original_h)
    pad_w = max(0, width - original_w)
    if pad_h or pad_w:
        image_rgb = cv2.copyMakeBorder(
            image_rgb, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT_101
        )
        if mask is not None:
            mask = cv2.copyMakeBorder(
                mask, 0, pad_h, 0, pad_w, cv2.BORDER_CONSTANT, value=0
            )
    return image_rgb, mask, original_h, original_w


def analyze_image_stats(image_bgr):
    """分析单张图像的亮度、对比度、阴影、噪声等特征"""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return {
        'brightness': float(gray.mean()),
        'contrast': float(gray.std()),
        'shadow_ratio': float((gray < 50).mean()),
        'highlight_ratio': float((gray > 200).mean()),
        'sharpness': float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        'entropy': float(shannon_entropy(gray)),
        'height': int(gray.shape[0]),
        'width': int(gray.shape[1]),
    }
