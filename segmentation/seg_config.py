# -*- coding: utf-8 -*-
"""分割模块公共配置"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data' / '02_processed_data'
RAW_DIR = ROOT / 'data'
WEIGHTS_DIR = ROOT / 'weights'
RUNS_DIR = ROOT / 'runs'

# DeepCrack 原始图像尺寸为 544x384（宽x高），统一按此尺寸做反射填充
PAD_HEIGHT = 384
PAD_WIDTH = 544
CROP_SIZE = 384

# ImageNet 归一化参数，与预训练骨干保持一致
IMAGE_MEAN = (0.485, 0.456, 0.406)
IMAGE_STD = (0.229, 0.224, 0.225)

# 两个待对比模型
MODEL_KEYS = ('deeplabv3plus_mobilenetv2', 'segformer_b0')

MODEL_LABELS = {
    'deeplabv3plus_mobilenetv2': 'DeepLabV3+ (MobileNetV2)',
    'segformer_b0': 'SegFormer-B0',
}

# 预处理模式
PREPROCESS_MODES = ('none', 'clahe', 'full')

# 默认推理阈值
DEFAULT_THRESHOLD = 0.5
