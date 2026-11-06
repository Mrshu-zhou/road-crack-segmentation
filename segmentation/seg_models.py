# -*- coding: utf-8 -*-
"""模型构建与权重加载"""

import os

# SMP / timm 的预训练权重托管在 HuggingFace，国内直连不稳定，优先走镜像
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')

import segmentation_models_pytorch as smp

MODEL_SPECS = {
    'deeplabv3plus_mobilenetv2': {
        'arch': 'deeplabv3plus',
        'encoder': 'mobilenet_v2',
        'label': 'DeepLabV3+ (MobileNetV2)',
    },
    'segformer_b0': {
        'arch': 'segformer',
        'encoder': 'mit_b0',
        'label': 'SegFormer-B0',
    },
}


def build_model(model_key, encoder_weights='imagenet', classes=1):
    """构建分割模型；encoder_weights=None 时用于加载本地权重"""
    if model_key not in MODEL_SPECS:
        raise ValueError(f'未知模型: {model_key}')
    spec = MODEL_SPECS[model_key]
    common = dict(
        encoder_name=spec['encoder'],
        encoder_weights=encoder_weights,
        in_channels=3,
        classes=classes,
    )
    if spec['arch'] == 'deeplabv3plus':
        return smp.DeepLabV3Plus(**common)
    if spec['arch'] == 'segformer':
        return smp.Segformer(**common)
    raise ValueError(f'未知网络结构: {spec["arch"]}')


def load_checkpoint(model_key, checkpoint_path, device='cpu'):
    """加载训练好的权重，返回模型与训练配置"""
    import torch

    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = build_model(model_key, encoder_weights=None, classes=1)
    model.load_state_dict(checkpoint['state_dict'])
    model.to(device)
    model.eval()
    return model, checkpoint
