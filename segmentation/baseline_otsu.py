# -*- coding: utf-8 -*-
"""
传统图像处理基线：Otsu 阈值 + 形态学后处理。

用于与深度学习模型对比，同时量化不同预处理对传统方法的影响。
"""

import json
from pathlib import Path

import cv2
import numpy as np
from skimage.morphology import closing, disk, remove_small_objects

from metrics import aggregate_metrics, compute_binary_metrics
from preprocessing import apply_preprocess
from seg_config import DATA_DIR, RUNS_DIR


def otsu_predict(image_bgr, preprocess_mode):
    """Otsu 反阈值提取暗色裂缝，再做小区域剔除与闭运算"""
    image_rgb = apply_preprocess(image_bgr, preprocess_mode)
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    mask = remove_small_objects(mask > 0, max_size=29, connectivity=2)
    mask = closing(mask, disk(1))
    return mask


def evaluate_dataset(split_dir, preprocess_mode):
    split_dir = Path(split_dir)
    metrics = []
    for image_path in sorted((split_dir / 'images').glob('*.jpg')):
        mask_path = split_dir / 'masks' / f'{image_path.stem}.png'
        image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        ground_truth = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if image_bgr is None or ground_truth is None:
            continue
        pred = otsu_predict(image_bgr, preprocess_mode)
        gt = ground_truth > 127
        metrics.append(compute_binary_metrics(pred, gt))
    return aggregate_metrics(metrics)


def main():
    datasets = {
        'deepcrack_test': DATA_DIR / 'DeepCrack' / 'test',
        'cfd_test': DATA_DIR / 'CFD' / 'test',
    }
    results = {}
    for dataset_name, split_dir in datasets.items():
        results[dataset_name] = {}
        for mode in ('none', 'clahe', 'full'):
            results[dataset_name][mode] = evaluate_dataset(split_dir, mode)
            print(f'{dataset_name} / {mode}: dice={results[dataset_name][mode]["dice"]:.4f}')

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RUNS_DIR / 'baseline_otsu.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
