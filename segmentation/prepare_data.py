# -*- coding: utf-8 -*-
"""
将 DeepCrack 与 CrackForest(CFD) 原始数据整理为统一目录结构。

输出结构：
  data/02_processed_data/DeepCrack/{train,val,test}/{images,masks}
  data/02_processed_data/CFD/test/{images,masks}
  data/02_processed_data/splits.json

DeepCrack 官方划分：train 300 张、test 237 张；从 train 中再切 30 张做验证集。
CFD 全部 118 张作为跨数据集测试集，用于观察域偏移下的泛化能力。
"""

import json
import random
import shutil
from pathlib import Path

import cv2
import numpy as np
import scipy.io as sio

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
RAW_DEEPCRACK = DATA / '01_raw_DeepCrack' / 'dataset' / 'extracted'
RAW_CFD = DATA / '01_raw_CFD'
PROCESSED = DATA / '02_processed_data'

RANDOM_SEED = 42
VAL_RATIO = 0.1


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _copy_pair(image_path: Path, mask_path: Path, out_split: Path, stem: str):
    """复制一对图像与掩码，并统一掩码为 0/255 单通道 PNG"""
    image_out = out_split / 'images' / f'{stem}.jpg'
    mask_out = out_split / 'masks' / f'{stem}.png'
    shutil.copyfile(image_path, image_out)

    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise RuntimeError(f'掩码读取失败: {mask_path}')
    mask = (mask > 127).astype(np.uint8) * 255
    cv2.imwrite(str(mask_out), mask)


def prepare_deepcrack():
    """整理 DeepCrack，并按 270/30/237 划分训练、验证、测试"""
    splits = {
        'train': RAW_DEEPCRACK / 'train_images',
        'test': RAW_DEEPCRACK / 'test_images',
    }
    out_root = PROCESSED / 'DeepCrack'

    train_pairs = sorted(
        (p, RAW_DEEPCRACK / 'train_masks' / f'{p.stem}.png')
        for p in splits['train'].glob('*.jpg')
    )
    if not train_pairs:
        raise RuntimeError('未找到 DeepCrack 训练图片，请检查原始数据目录')

    random.Random(RANDOM_SEED).shuffle(train_pairs)
    val_count = max(1, int(len(train_pairs) * VAL_RATIO))
    val_pairs = train_pairs[:val_count]
    train_pairs = train_pairs[val_count:]

    for split_name, pairs in (('train', train_pairs), ('val', val_pairs)):
        out_split = out_root / split_name
        _ensure_dir(out_split / 'images')
        _ensure_dir(out_split / 'masks')
        for image_path, mask_path in pairs:
            _copy_pair(image_path, mask_path, out_split, image_path.stem)

    out_split = out_root / 'test'
    _ensure_dir(out_split / 'images')
    _ensure_dir(out_split / 'masks')
    test_pairs = sorted(
        (p, RAW_DEEPCRACK / 'test_masks' / f'{p.stem}.png')
        for p in splits['test'].glob('*.jpg')
    )
    for image_path, mask_path in test_pairs:
        _copy_pair(image_path, mask_path, out_split, image_path.stem)

    return {
        'train': len(train_pairs),
        'val': len(val_pairs),
        'test': len(test_pairs),
    }


def _load_cfd_mask(mat_path: Path) -> np.ndarray:
    """从 CFD 的 .mat 结构体中取出 Segmentation 掩码"""
    data = sio.loadmat(str(mat_path), squeeze_me=True, struct_as_record=False)
    ground_truth = data['groundTruth']
    segmentation = np.asarray(ground_truth.Segmentation)
    # CFD 标注中 1 = 背景，2 = 裂缝
    return (segmentation == 2).astype(np.uint8) * 255


def prepare_cfd():
    """整理 CFD 跨域测试集"""
    out_split = PROCESSED / 'CFD' / 'test'
    _ensure_dir(out_split / 'images')
    _ensure_dir(out_split / 'masks')

    processed = 0
    for image_path in sorted((RAW_CFD / 'images').glob('*.jpg')):
        mat_path = RAW_CFD / 'ground_truth_mat' / f'{image_path.stem}.mat'
        if not mat_path.exists():
            continue
        shutil.copyfile(image_path, out_split / 'images' / image_path.name)
        mask = _load_cfd_mask(mat_path)
        cv2.imwrite(str(out_split / 'masks' / f'{image_path.stem}.png'), mask)
        processed += 1
    return processed


def main():
    _ensure_dir(PROCESSED)
    deepcrack_stats = prepare_deepcrack()
    cfd_count = prepare_cfd()

    meta = {
        'random_seed': RANDOM_SEED,
        'val_ratio': VAL_RATIO,
        'deepcrack': deepcrack_stats,
        'cfd_test': cfd_count,
        'note': 'DeepCrack 用于训练与同域测试，CFD 仅作为跨域测试集',
    }
    with open(PROCESSED / 'splits.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
