# -*- coding: utf-8 -*-
"""
数据集图像特征分析。

输出：
  runs/image_analysis.json   各数据集亮度/对比度/阴影/清晰度/裂缝占比统计
  runs/image_analysis.md     可直接放入实验报告
  runs/preprocess_demo.jpg   原图 / CLAHE / Retinex 三栏对比图
"""

import json
from pathlib import Path

import cv2
import numpy as np

from preprocessing import analyze_image_stats, apply_preprocess
from seg_config import DATA_DIR, RUNS_DIR


def analyze_split(split_dir):
    split_dir = Path(split_dir)
    stats_list = []
    crack_ratios = []
    for image_path in sorted((split_dir / 'images').glob('*.jpg')):
        image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        mask = cv2.imread(str(split_dir / 'masks' / f'{image_path.stem}.png'), cv2.IMREAD_GRAYSCALE)
        if image_bgr is None or mask is None:
            continue
        stats_list.append(analyze_image_stats(image_bgr))
        crack_ratios.append(float((mask > 127).mean()))

    keys = ('brightness', 'contrast', 'shadow_ratio', 'highlight_ratio', 'sharpness', 'entropy')
    summary = {
        key: {
            'mean': float(np.mean([item[key] for item in stats_list])),
            'std': float(np.std([item[key] for item in stats_list])),
        }
        for key in keys
    }
    summary['crack_pixel_ratio'] = {
        'mean': float(np.mean(crack_ratios)),
        'max': float(np.max(crack_ratios)) if crack_ratios else 0.0,
    }
    summary['num_images'] = len(stats_list)
    summary['resolution'] = {
        'height_mean': float(np.mean([item['height'] for item in stats_list])),
        'width_mean': float(np.mean([item['width'] for item in stats_list])),
    }
    return summary


def save_preprocess_demo(split_dir, output_path, count=3):
    """挑选若干张图，横向拼接原图 / CLAHE / full 三种结果"""
    image_paths = sorted((Path(split_dir) / 'images').glob('*.jpg'))[:count]
    rows = []
    for image_path in image_paths:
        image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image_bgr is None:
            continue
        target_w = 360
        scale = target_w / image_bgr.shape[1]
        image_bgr = cv2.resize(image_bgr, (target_w, int(image_bgr.shape[0] * scale)))
        panels = [('Original', image_bgr)]
        for mode in ('clahe', 'full'):
            enhanced = cv2.cvtColor(apply_preprocess(image_bgr, mode), cv2.COLOR_RGB2BGR)
            panels.append((mode.upper(), enhanced))
        row = []
        for label, panel in panels:
            cv2.putText(panel, label, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            row.append(panel)
        rows.append(np.concatenate(row, axis=1))
    if rows:
        cv2.imwrite(str(output_path), np.concatenate(rows, axis=0))
        print(f'预处理对比图已保存: {output_path}')


def main():
    datasets = {
        'DeepCrack train': DATA_DIR / 'DeepCrack' / 'train',
        'DeepCrack val': DATA_DIR / 'DeepCrack' / 'val',
        'DeepCrack test': DATA_DIR / 'DeepCrack' / 'test',
        'CFD test (跨域)': DATA_DIR / 'CFD' / 'test',
    }
    results = {name: analyze_split(path) for name, path in datasets.items()}

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RUNS_DIR / 'image_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    lines = ['# 数据集图像特征分析', '', '| 数据集 | 图像数 | 分辨率 | 亮度 | 对比度 | 阴影占比 | 高光占比 | 清晰度 | 熵 | 裂缝像素占比 |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for name, item in results.items():
        resolution = f"{item['resolution']['width_mean']:.0f}x{item['resolution']['height_mean']:.0f}"
        lines.append(
            f"| {name} | {item['num_images']} | {resolution} | "
            f"{item['brightness']['mean']:.1f} | {item['contrast']['mean']:.1f} | "
            f"{item['shadow_ratio']['mean'] * 100:.1f}% | {item['highlight_ratio']['mean'] * 100:.1f}% | "
            f"{item['sharpness']['mean']:.1f} | {item['entropy']['mean']:.2f} | "
            f"{item['crack_pixel_ratio']['mean'] * 100:.2f}% |"
        )
    with open(RUNS_DIR / 'image_analysis.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    save_preprocess_demo(DATA_DIR / 'DeepCrack' / 'test', RUNS_DIR / 'preprocess_demo.jpg')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
