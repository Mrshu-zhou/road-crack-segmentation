# -*- coding: utf-8 -*-
"""二值分割指标"""

import numpy as np
from skimage.morphology import dilation, disk
from skimage.segmentation import find_boundaries

EPS = 1e-8


def compute_binary_metrics(pred, gt, boundary_dilation=2):
    """计算单张图像的 IoU/Dice/Precision/Recall/边界 IoU"""
    pred = np.asarray(pred, dtype=bool)
    gt = np.asarray(gt, dtype=bool)

    tp = int(np.sum(pred & gt))
    fp = int(np.sum(pred & ~gt))
    fn = int(np.sum(~pred & gt))

    iou = tp / (tp + fp + fn + EPS)
    dice = (2 * tp) / (2 * tp + fp + fn + EPS)
    precision = tp / (tp + fp + EPS)
    recall = tp / (tp + fn + EPS)

    if not pred.any() and not gt.any():
        boundary_iou = 1.0
    else:
        pred_boundary = find_boundaries(pred, mode='outer')
        gt_boundary = find_boundaries(gt, mode='outer')
        pred_band = dilation(pred_boundary, disk(boundary_dilation))
        gt_band = dilation(gt_boundary, disk(boundary_dilation))
        union = np.sum(pred_band | gt_band)
        boundary_iou = float(np.sum(pred_band & gt_band) / union) if union else 1.0

    return {
        'iou': float(iou),
        'dice': float(dice),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(dice),
        'boundary_iou': float(boundary_iou),
        'tp': tp,
        'fp': fp,
        'fn': fn,
    }


def aggregate_metrics(metric_list):
    """逐图指标取平均，并汇总像素级全局指标"""
    if not metric_list:
        return {}
    keys = ('iou', 'dice', 'precision', 'recall', 'f1', 'boundary_iou')
    result = {key: float(np.mean([m[key] for m in metric_list])) for key in keys}
    tp = sum(m['tp'] for m in metric_list)
    fp = sum(m['fp'] for m in metric_list)
    fn = sum(m['fn'] for m in metric_list)
    result['global_iou'] = float(tp / (tp + fp + fn + EPS))
    result['global_dice'] = float((2 * tp) / (2 * tp + fp + fn + EPS))
    result['global_precision'] = float(tp / (tp + fp + EPS))
    result['global_recall'] = float(tp / (tp + fn + EPS))
    result['num_images'] = len(metric_list)
    return result
