# -*- coding: utf-8 -*-
"""
导出 ONNX 并测量 CPU 推理耗时。

输出：exports/<model_key>.onnx、runs/onnx_latency.json
"""

import json
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch

from seg_config import RUNS_DIR, WEIGHTS_DIR
from seg_models import build_model

EXPORT_DIR = Path(__file__).resolve().parent / 'exports'
INPUT_SIZE = (1, 3, 384, 544)


def export_one(model_key):
    weights = WEIGHTS_DIR / f'{model_key}_best.pth'
    if not weights.exists():
        return {'model_key': model_key, 'error': '权重不存在'}

    checkpoint = torch.load(weights, map_location='cpu', weights_only=False)
    model = build_model(model_key, encoder_weights=None, classes=1)
    model.load_state_dict(checkpoint['state_dict'])
    model.eval()

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    onnx_path = EXPORT_DIR / f'{model_key}.onnx'
    dummy = torch.randn(*INPUT_SIZE)
    try:
        torch.onnx.export(
            model, dummy, str(onnx_path),
            input_names=['input'], output_names=['logits'],
            opset_version=17, dynamo=False,
        )
    except TypeError:
        torch.onnx.export(
            model, dummy, str(onnx_path),
            input_names=['input'], output_names=['logits'],
            opset_version=17,
        )

    session = ort.InferenceSession(str(onnx_path), providers=['CPUExecutionProvider'])
    input_name = session.get_inputs()[0].name
    tensor = np.random.randn(*INPUT_SIZE).astype(np.float32)
    for _ in range(3):
        session.run(None, {input_name: tensor})

    runs = 10
    start = time.time()
    for _ in range(runs):
        session.run(None, {input_name: tensor})
    latency_ms = (time.time() - start) / runs * 1000.0

    return {
        'model_key': model_key,
        'onnx_path': str(onnx_path),
        'size_mb': round(onnx_path.stat().st_size / 1024 / 1024, 2),
        'cpu_latency_ms': round(latency_ms, 2),
        'input_size': list(INPUT_SIZE),
    }


def main():
    results = [export_one(model_key) for model_key in ('deeplabv3plus_mobilenetv2', 'segformer_b0')]
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RUNS_DIR / 'onnx_latency.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
