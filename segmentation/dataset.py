# -*- coding: utf-8 -*-
"""裂缝分割数据集与数据增强"""

from pathlib import Path

import albumentations as A
import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from seg_config import CROP_SIZE, PAD_HEIGHT, PAD_WIDTH
from preprocessing import apply_preprocess, normalize_image, pad_to_size


def _build_train_augmentation():
    """训练增强：只做几何与轻度光照扰动，避免破坏细小裂缝"""
    return A.Compose([
        A.RandomCrop(height=CROP_SIZE, width=CROP_SIZE, p=1.0),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.3),
        A.Rotate(limit=15, border_mode=cv2.BORDER_REFLECT_101, p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
        A.GaussianBlur(blur_limit=(3, 5), p=0.2),
        A.GaussNoise(p=0.2),
    ])


class CrackDataset(Dataset):
    """读取 images/masks 目录下同名的图像与掩码"""

    def __init__(self, split_dir, preprocess_mode='full', augment=False):
        self.split_dir = Path(split_dir)
        self.image_paths = sorted((self.split_dir / 'images').glob('*.jpg'))
        if not self.image_paths:
            raise RuntimeError(f'目录下没有图像: {self.split_dir}')
        self.mask_dir = self.split_dir / 'masks'
        self.preprocess_mode = preprocess_mode
        self.transform = _build_train_augmentation() if augment else None

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, index):
        image_path = self.image_paths[index]
        mask_path = self.mask_dir / f'{image_path.stem}.png'

        image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if image_bgr is None or mask is None:
            raise RuntimeError(f'读取失败: {image_path} 或 {mask_path}')

        # DeepCrack 测试集包含 47 张竖版（旋转 90°）图像，统一转回横向
        if image_bgr.shape[0] > image_bgr.shape[1]:
            image_bgr = cv2.rotate(image_bgr, cv2.ROTATE_90_CLOCKWISE)
            mask = cv2.rotate(mask, cv2.ROTATE_90_CLOCKWISE)

        image = apply_preprocess(image_bgr, self.preprocess_mode)
        mask = (mask > 127).astype(np.uint8) * 255
        image, mask, valid_h, valid_w = pad_to_size(
            image, mask, height=PAD_HEIGHT, width=PAD_WIDTH
        )

        if self.transform is not None:
            transformed = self.transform(image=image, mask=mask)
            image = transformed['image']
            mask = transformed['mask']

        image = normalize_image(image)
        mask = (mask > 127).astype(np.float32)[None, :, :]

        return {
            'image': torch.from_numpy(image),
            'mask': torch.from_numpy(mask),
            'stem': image_path.stem,
            'valid_h': valid_h,
            'valid_w': valid_w,
        }


def build_dataloader(
    split_dir,
    preprocess_mode='full',
    augment=False,
    batch_size=8,
    num_workers=4,
    shuffle=False,
):
    dataset = CrackDataset(split_dir, preprocess_mode=preprocess_mode, augment=augment)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
        persistent_workers=num_workers > 0,
    )
    return dataset, loader
