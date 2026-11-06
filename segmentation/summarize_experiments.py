# -*- coding: utf-8 -*-
"""
汇总训练、评估与消融结果，生成 runs/experiments_summary.json，供前端图表使用。
"""

import json
from datetime import datetime
from pathlib import Path

from seg_config import RUNS_DIR, WEIGHTS_DIR
from seg_models import build_model

MODELS = {
    'deeplabv3plus_mobilenetv2': 'DeepLabV3+ (MobileNetV2)',
    'segformer_b0': 'SegFormer-B0',
}

EVAL_FILES = {
    'deeplabv3plus_mobilenetv2': {
        'deepcrack': 'eval_deeplab_deepcrack',
        'cfd': 'eval_deeplab_cfd',
    },
    'segformer_b0': {
        'deepcrack': 'eval_segformer_deepcrack',
        'cfd': 'eval_segformer_cfd',
    },
}

ABLATION_RUNS = [
    ('预处理', 'none', 'ablation_preprocess_none', '关闭 CLAHE/Retinex，仅 RGB'),
    ('预处理', 'clahe', 'ablation_preprocess_clahe', '仅 CLAHE + 双边滤波'),
    ('损失函数', 'BCE', 'ablation_loss_bce', '仅二值交叉熵'),
    ('损失函数', 'Dice', 'ablation_loss_dice', '仅软 Dice'),
    ('数据增强', '关闭增强', 'ablation_noaug', '不做翻转/裁剪/光照扰动'),
]


def load_json(path):
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_eval_metrics(model_key, dataset):
    path = RUNS_DIR / EVAL_FILES[model_key][dataset] / 'metrics.json'
    data = load_json(path)
    if not data:
        return None
    return data


def get_ablation_metrics(run_tag):
    """优先读取测试集评估，缺失时回退到训练时的验证集指标"""
    eval_path = RUNS_DIR / f'eval_{run_tag}' / 'metrics.json'
    data = load_json(eval_path)
    if data:
        return data.get('postprocess') or data.get('raw'), '测试集'
    train_path = RUNS_DIR / run_tag / 'metrics.json'
    data = load_json(train_path)
    if data:
        return data.get('val_metrics'), '验证集'
    return None, ''


def count_parameters(model_key):
    model = build_model(model_key, encoder_weights=None, classes=1)
    return round(sum(parameter.numel() for parameter in model.parameters()) / 1e6, 2)


def main():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    onnx_latency = {
        item['model_key']: item
        for item in (load_json(RUNS_DIR / 'onnx_latency.json') or [])
        if 'model_key' in item
    }

    models = []
    threshold_sweep = None
    for model_key, label in MODELS.items():
        deepcrack_eval = get_eval_metrics(model_key, 'deepcrack')
        cfd_eval = get_eval_metrics(model_key, 'cfd')
        item = {
            'model_key': model_key,
            'label': label,
            'params_m': count_parameters(model_key),
            'weights_exists': (WEIGHTS_DIR / f'{model_key}_best.pth').exists(),
            'deepcrack': (deepcrack_eval or {}).get('postprocess'),
            'cfd': (cfd_eval or {}).get('postprocess'),
            'latency_ms': (deepcrack_eval or {}).get('latency_ms_per_image'),
            'cpu_latency_ms': onnx_latency.get(model_key, {}).get('cpu_latency_ms'),
            'onnx_size_mb': onnx_latency.get(model_key, {}).get('size_mb'),
        }
        models.append(item)
        if model_key == 'deeplabv3plus_mobilenetv2' and deepcrack_eval:
            threshold_sweep = deepcrack_eval.get('threshold_sweep')

    ablation = []
    main_eval = get_eval_metrics('deeplabv3plus_mobilenetv2', 'deepcrack')
    if main_eval:
        raw = main_eval.get('raw') or {}
        post = main_eval.get('postprocess') or {}
        ablation.append({
            'group': '主模型', 'name': 'full + BCE+Dice + 增强',
            'iou': raw.get('iou'), 'dice': raw.get('dice'),
            'boundary_iou': raw.get('boundary_iou'), 'note': 'DeepCrack 测试集，未后处理',
        })
        ablation.append({
            'group': '后处理', 'name': '阈值 0.5',
            'iou': raw.get('iou'), 'dice': raw.get('dice'),
            'boundary_iou': raw.get('boundary_iou'), 'note': '原始概率阈值化',
        })
        ablation.append({
            'group': '后处理', 'name': '形态学后处理',
            'iou': post.get('iou'), 'dice': post.get('dice'),
            'boundary_iou': post.get('boundary_iou'), 'note': '去小连通域 + 闭运算',
        })

    for group, name, run_tag, note in ABLATION_RUNS:
        metrics, source = get_ablation_metrics(run_tag)
        if not metrics:
            continue
        ablation.append({
            'group': group, 'name': name,
            'iou': metrics.get('iou'), 'dice': metrics.get('dice'),
            'boundary_iou': metrics.get('boundary_iou'),
            'note': f'{note}（{source}）',
        })

    baselines = load_json(RUNS_DIR / 'baseline_otsu.json') or {}

    summary = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'models': models,
        'ablation': ablation,
        'baselines': baselines,
        'threshold_sweep': threshold_sweep,
    }
    with open(RUNS_DIR / 'experiments_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
