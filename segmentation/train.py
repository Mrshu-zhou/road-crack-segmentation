# -*- coding: utf-8 -*-
"""
裂缝分割模型训练脚本。

用法示例：
  python train.py --model deeplabv3plus_mobilenetv2 --preprocess full --loss bce_dice --epochs 40
  python train.py --model segformer_b0 --preprocess full --loss bce_dice --epochs 40
  python train.py --model deeplabv3plus_mobilenetv2 --preprocess none --loss bce_dice --run-name ablation_preprocess_none

每次训练会在 runs/<run_name>/ 下保存 history.csv、metrics.json 与 best.pth。
"""

import argparse
import csv
import json
import os
import random
import shutil
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

from seg_config import DATA_DIR, PAD_HEIGHT, PAD_WIDTH, RUNS_DIR, WEIGHTS_DIR
from dataset import build_dataloader
from metrics import aggregate_metrics, compute_binary_metrics
from seg_models import build_model


class DiceLoss(nn.Module):
    """软 Dice 损失，缓解裂缝像素占比极低的正负样本失衡"""

    def __init__(self, smooth=1e-6):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits, targets):
        probabilities = torch.sigmoid(logits)
        intersection = (probabilities * targets).sum(dim=(2, 3))
        union = probabilities.sum(dim=(2, 3)) + targets.sum(dim=(2, 3))
        dice = (2 * intersection + self.smooth) / (union + self.smooth)
        return 1 - dice.mean()


class FocalLoss(nn.Module):
    """二分类 Focal Loss"""

    def __init__(self, alpha=0.25, gamma=2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits, targets):
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction='none')
        pt = torch.exp(-bce)
        focal = self.alpha * (1 - pt) ** self.gamma * bce
        return focal.mean()


class CombinedLoss(nn.Module):
    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss()
        self.focal = FocalLoss()

    def forward(self, logits, targets):
        if self.kind == 'bce':
            return self.bce(logits, targets)
        if self.kind == 'dice':
            return self.dice(logits, targets)
        if self.kind == 'focal_dice':
            return 0.5 * self.focal(logits, targets) + 0.5 * self.dice(logits, targets)
        return 0.5 * self.bce(logits, targets) + 0.5 * self.dice(logits, targets)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def evaluate(model, loader, device, threshold=0.5):
    model.eval()
    metric_list = []
    with torch.no_grad():
        for batch in loader:
            images = batch['image'].to(device, non_blocking=True)
            masks = batch['mask'].to(device, non_blocking=True)
            logits = model(images)
            probabilities = torch.sigmoid(logits)
            for index in range(images.size(0)):
                valid_h = int(batch['valid_h'][index])
                valid_w = int(batch['valid_w'][index])
                pred = probabilities[index, 0, :valid_h, :valid_w].cpu().numpy() >= threshold
                gt = masks[index, 0, :valid_h, :valid_w].cpu().numpy() > 0.5
                metric_list.append(compute_binary_metrics(pred, gt))
    return aggregate_metrics(metric_list)


def parse_args():
    parser = argparse.ArgumentParser(description='裂缝分割训练')
    parser.add_argument('--model', required=True, choices=['deeplabv3plus_mobilenetv2', 'segformer_b0'])
    parser.add_argument('--preprocess', default='full', choices=['none', 'clahe', 'full'])
    parser.add_argument('--loss', default='bce_dice', choices=['bce', 'dice', 'bce_dice', 'focal_dice'])
    parser.add_argument('--no-aug', action='store_true', help='关闭数据增强，用于消融实验')
    parser.add_argument('--epochs', type=int, default=40)
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--weight-decay', type=float, default=1e-4)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--num-workers', type=int, default=4)
    parser.add_argument('--val-every', type=int, default=1)
    parser.add_argument('--patience', type=int, default=12)
    parser.add_argument('--data-root', default=str(DATA_DIR / 'DeepCrack'))
    parser.add_argument('--run-name', default='')
    parser.add_argument('--weights-name', default='', help='额外保存到 weights/ 下的文件名')
    parser.add_argument('--resume', default='', help='从指定 checkpoint 继续训练')
    return parser.parse_args()


def main():
    args = parse_args()
    set_seed(args.seed)
    os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')

    run_name = args.run_name or (
        f'{args.model}_{args.preprocess}_{args.loss}' + ('_noaug' if args.no_aug else '')
    )
    run_dir = RUNS_DIR / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    use_amp = device.type == 'cuda'

    data_root = Path(args.data_root)
    train_dir = data_root / 'train'
    val_dir = data_root / 'val'

    _, train_loader = build_dataloader(
        train_dir, preprocess_mode=args.preprocess, augment=not args.no_aug,
        batch_size=args.batch_size, num_workers=args.num_workers, shuffle=True,
    )
    _, val_loader = build_dataloader(
        val_dir, preprocess_mode=args.preprocess, augment=False,
        batch_size=max(1, args.batch_size // 2), num_workers=args.num_workers, shuffle=False,
    )

    model = build_model(args.model, encoder_weights='imagenet').to(device)
    criterion = CombinedLoss(args.loss)

    encoder_parameters = []
    decoder_parameters = []
    for name, parameter in model.named_parameters():
        if name.startswith('encoder'):
            encoder_parameters.append(parameter)
        else:
            decoder_parameters.append(parameter)
    optimizer = AdamW([
        {'params': encoder_parameters, 'lr': args.lr * 0.1},
        {'params': decoder_parameters, 'lr': args.lr},
    ], weight_decay=args.weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    scaler = torch.amp.GradScaler('cuda', enabled=use_amp)

    start_epoch = 1
    best_dice = -1.0
    if args.resume and Path(args.resume).exists():
        checkpoint = torch.load(args.resume, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint['state_dict'])
        start_epoch = checkpoint.get('epoch', 0) + 1
        best_dice = checkpoint.get('best_dice', -1.0)

    history_path = run_dir / 'history.csv'
    if start_epoch == 1 or not history_path.exists():
        with open(history_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['epoch', 'train_loss', 'val_iou', 'val_dice', 'val_precision', 'val_recall',
                             'val_boundary_iou', 'lr', 'seconds'])

    model.train()
    patience_counter = 0
    for epoch in range(start_epoch, args.epochs + 1):
        epoch_start = time.time()
        running_loss = 0.0
        model.train()
        for step, batch in enumerate(train_loader, 1):
            images = batch['image'].to(device, non_blocking=True)
            masks = batch['mask'].to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast('cuda', enabled=use_amp, dtype=torch.float16):
                logits = model(images)
                loss = criterion(logits, masks)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item()
            if step % 10 == 0:
                print(f'[epoch {epoch}/{args.epochs}] step {step}/{len(train_loader)} loss={loss.item():.4f}', flush=True)

        scheduler.step()
        train_loss = running_loss / max(1, len(train_loader))
        elapsed = time.time() - epoch_start

        if epoch % args.val_every == 0 or epoch == args.epochs:
            val_metrics = evaluate(model, val_loader, device)
            print(
                f'[epoch {epoch}] loss={train_loss:.4f} val_iou={val_metrics["iou"]:.4f} '
                f'val_dice={val_metrics["dice"]:.4f} time={elapsed:.1f}s', flush=True
            )
            with open(history_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    epoch, f'{train_loss:.6f}', f'{val_metrics["iou"]:.6f}',
                    f'{val_metrics["dice"]:.6f}', f'{val_metrics["precision"]:.6f}',
                    f'{val_metrics["recall"]:.6f}', f'{val_metrics["boundary_iou"]:.6f}',
                    f'{optimizer.param_groups[-1]["lr"]:.8f}', f'{elapsed:.2f}',
                ])

            if val_metrics['dice'] > best_dice:
                best_dice = val_metrics['dice']
                patience_counter = 0
                checkpoint = {
                    'model_key': args.model,
                    'state_dict': model.state_dict(),
                    'preprocess_mode': args.preprocess,
                    'loss': args.loss,
                    'augment': not args.no_aug,
                    'epoch': epoch,
                    'best_dice': best_dice,
                    'val_metrics': val_metrics,
                    'args': vars(args),
                }
                torch.save(checkpoint, run_dir / 'best.pth')
                print(f'  保存最佳权重: {run_dir / "best.pth"} (dice={best_dice:.4f})', flush=True)
            else:
                patience_counter += 1
                if patience_counter >= args.patience:
                    print(f'验证指标连续 {args.patience} 轮未提升，提前结束', flush=True)
                    break
        else:
            print(f'[epoch {epoch}] loss={train_loss:.4f} time={elapsed:.1f}s', flush=True)

    best_path = run_dir / 'best.pth'
    if best_path.exists():
        if args.weights_name:
            shutil.copyfile(best_path, WEIGHTS_DIR / args.weights_name)
            print(f'权重已复制到: {WEIGHTS_DIR / args.weights_name}')
        checkpoint = torch.load(best_path, map_location='cpu', weights_only=False)
        summary = {
            'run_name': run_name,
            'model_key': args.model,
            'preprocess_mode': args.preprocess,
            'loss': args.loss,
            'augment': not args.no_aug,
            'best_epoch': checkpoint.get('epoch'),
            'val_metrics': checkpoint.get('val_metrics', {}),
            'args': vars(args),
        }
        with open(run_dir / 'metrics.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
