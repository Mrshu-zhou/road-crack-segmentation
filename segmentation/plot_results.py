# -*- coding: utf-8 -*-
"""
绘制训练曲线与消融对比图，输出到 runs/ 下，供实验报告使用。
"""

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from seg_config import RUNS_DIR

# 支持图表中的中文标签
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

MAIN_RUNS = {
    'DeepLabV3+': 'deeplabv3plus_mobilenetv2_full_bce_dice',
    'SegFormer-B0': 'segformer_b0_full_bce_dice',
}


def read_history(run_name):
    path = RUNS_DIR / run_name / 'history.csv'
    if not path.exists():
        return None
    epochs, losses, dices = [], [], []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            epochs.append(int(row['epoch']))
            losses.append(float(row['train_loss']))
            dices.append(float(row['val_dice']))
    return epochs, losses, dices


def plot_training_curves():
    figure, axes = plt.subplots(1, 2, figsize=(12, 4))
    for label, run_name in MAIN_RUNS.items():
        history = read_history(run_name)
        if not history:
            continue
        epochs, losses, dices = history
        axes[0].plot(epochs, losses, label=label)
        axes[1].plot(epochs, dices, label=label)
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Train loss')
    axes[0].set_title('Training loss')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Validation Dice')
    axes[1].set_title('Validation Dice')
    axes[0].legend()
    axes[1].legend()
    axes[0].grid(alpha=0.3)
    axes[1].grid(alpha=0.3)
    figure.tight_layout()
    output = RUNS_DIR / 'training_curves.png'
    figure.savefig(output, dpi=160)
    plt.close(figure)
    print(f'训练曲线已保存: {output}')


def plot_ablation():
    summary_path = RUNS_DIR / 'experiments_summary.json'
    if not summary_path.exists():
        print('experiments_summary.json 不存在，跳过消融图')
        return
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)

    rows = [row for row in summary.get('ablation', []) if row.get('dice') is not None]
    if not rows:
        print('没有可绘制的消融数据')
        return

    labels = [f"{row['group']}-{row['name']}" for row in rows]
    dices = [row['dice'] for row in rows]
    colors = ['#409eff' if row['group'] == '主模型' else '#67c23a' for row in rows]

    figure, axis = plt.subplots(figsize=(11, 4.5))
    axis.bar(range(len(rows)), dices, color=colors)
    axis.set_xticks(range(len(rows)))
    axis.set_xticklabels(labels, rotation=25, ha='right')
    axis.set_ylabel('Dice')
    axis.set_title('Ablation study (DeepCrack test set)')
    axis.grid(axis='y', alpha=0.3)
    for index, value in enumerate(dices):
        axis.text(index, value + 0.01, f'{value:.3f}', ha='center', fontsize=8)
    figure.tight_layout()
    output = RUNS_DIR / 'ablation_chart.png'
    figure.savefig(output, dpi=160)
    plt.close(figure)
    print(f'消融对比图已保存: {output}')


def main():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    plot_training_curves()
    plot_ablation()


if __name__ == '__main__':
    main()
