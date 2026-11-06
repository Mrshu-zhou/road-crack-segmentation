# -*- coding: utf-8 -*-
"""
模型评估脚本：输出原始/后处理指标、阈值扫描与可视化样例。

用法：
  python evaluate.py --checkpoint runs/deeplabv3plus_mobilenetv2_full_bce_dice/best.pth \
      --data data/02_processed_data/DeepCrack/test --output runs/eval_deeplab_deepcrack
  python evaluate.py --checkpoint runs/segformer_b0_full_bce_dice/best.pth \
      --data data/02_processed_data/CFD/test --output runs/eval_segformer_cfd
"""

import argparse
import csv
import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch

from seg_config import DEFAULT_THRESHOLD
from dataset import build_dataloader
from metrics import aggregate_metrics, compute_binary_metrics
from seg_models import build_model
from postprocess import postprocess_mask


def parse_args():
    parser = argparse.ArgumentParser(description='分割模型评估')
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--data', required=True)
    parser.add_argument('--output', default='')
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--num-workers', type=int, default=4)
    parser.add_argument('--threshold', type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument('--visualize', type=int, default=6)
    return parser.parse_args()


def _overlay(image_bgr, mask, color):
    """在原图上叠加半透明颜色与轮廓"""
    canvas = image_bgr.copy()
    layer = np.zeros_like(canvas)
    layer[mask] = color
    canvas = cv2.addWeighted(canvas, 0.65, layer, 0.35, 0)
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(canvas, contours, -1, color, 1)
    return canvas


def _save_visual(image_path, gt, pred, out_path):
    image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image_bgr is None:
        return
    if image_bgr.shape[0] > image_bgr.shape[1]:
        image_bgr = cv2.rotate(image_bgr, cv2.ROTATE_90_CLOCKWISE)
    gt_rgb = cv2.cvtColor((gt.astype(np.uint8) * 255), cv2.COLOR_GRAY2BGR)
    pred_overlay = _overlay(image_bgr, pred, (0, 0, 255))
    gt_overlay = _overlay(image_bgr, gt, (0, 255, 0))
    height, width = image_bgr.shape[:2]
    panels = [
        ('Image', image_bgr),
        ('Ground Truth', gt_overlay),
        ('Prediction', pred_overlay),
        ('GT Binary', gt_rgb),
    ]
    panel_list = []
    for title, panel in panels:
        panel = cv2.resize(panel, (width, height))
        cv2.putText(panel, title, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        panel_list.append(panel)
    cv2.imwrite(str(out_path), np.concatenate(panel_list, axis=1))


def main():
    args = parse_args()
    checkpoint_path = Path(args.checkpoint)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # 从 checkpoint 中读取 model_key 与预处理模式，再加载模型
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model_key = checkpoint['model_key']
    preprocess_mode = checkpoint.get('preprocess_mode', 'full')
    model = build_model(model_key, encoder_weights=None, classes=1)
    model.load_state_dict(checkpoint['state_dict'])
    model.to(device)
    model.eval()

    dataset, loader = build_dataloader(
        args.data, preprocess_mode=preprocess_mode, augment=False,
        batch_size=args.batch_size, num_workers=args.num_workers, shuffle=False,
    )

    output_dir = Path(args.output) if args.output else Path('runs') / f'eval_{model_key}'
    output_dir.mkdir(parents=True, exist_ok=True)
    visual_dir = output_dir / 'visuals'
    visual_dir.mkdir(parents=True, exist_ok=True)

    raw_metrics = []
    post_metrics = []
    per_image_rows = []
    sweep_preds = {t: [] for t in (0.3, 0.4, 0.5, 0.6, 0.7)}
    total_time = 0.0
    image_count = 0
    global_index = 0

    # 预热
    if device.type == 'cuda':
        dummy = torch.zeros(1, 3, 384, 544, device=device)
        with torch.no_grad():
            model(dummy)
        torch.cuda.synchronize()

    model.eval()
    with torch.no_grad():
        for batch in loader:
            images = batch['image'].to(device, non_blocking=True)
            masks = batch['mask'].to(device, non_blocking=True)

            if device.type == 'cuda':
                torch.cuda.synchronize()
            start = time.time()
            logits = model(images)
            probabilities = torch.sigmoid(logits).cpu().numpy()
            if device.type == 'cuda':
                torch.cuda.synchronize()
            total_time += time.time() - start

            for index in range(images.size(0)):
                valid_h = int(batch['valid_h'][index])
                valid_w = int(batch['valid_w'][index])
                prob = probabilities[index, 0, :valid_h, :valid_w]
                gt = masks[index, 0, :valid_h, :valid_w].cpu().numpy() > 0.5

                raw_pred = prob >= args.threshold
                raw = compute_binary_metrics(raw_pred, gt)
                raw_metrics.append(raw)

                post_pred = postprocess_mask(prob, threshold=args.threshold)
                post = compute_binary_metrics(post_pred, gt)
                post_metrics.append(post)

                for threshold in sweep_preds:
                    sweep_preds[threshold].append(
                        compute_binary_metrics(prob >= threshold, gt)
                    )

                stem = batch['stem'][index]
                per_image_rows.append({
                    'stem': stem,
                    'iou': raw['iou'],
                    'dice': raw['dice'],
                    'precision': raw['precision'],
                    'recall': raw['recall'],
                    'boundary_iou': raw['boundary_iou'],
                    'post_iou': post['iou'],
                    'post_dice': post['dice'],
                })

                if global_index < args.visualize:
                    _save_visual(
                        dataset.image_paths[global_index], gt, post_pred,
                        visual_dir / f'{stem}.png',
                    )
                global_index += 1

            image_count += images.size(0)

    summary = {
        'checkpoint': str(checkpoint_path),
        'model_key': model_key,
        'preprocess_mode': preprocess_mode,
        'data': str(args.data),
        'threshold': args.threshold,
        'raw': aggregate_metrics(raw_metrics),
        'postprocess': aggregate_metrics(post_metrics),
        'threshold_sweep': {
            str(t): aggregate_metrics(metrics) for t, metrics in sweep_preds.items()
        },
        'latency_ms_per_image': float(total_time / max(1, image_count) * 1000),
        'num_images': image_count,
    }

    with open(output_dir / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with open(output_dir / 'per_image.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(per_image_rows[0].keys()))
        writer.writeheader()
        writer.writerows(per_image_rows)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
