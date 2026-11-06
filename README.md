# 道路巡检缺陷检测系统

面向道路巡检场景的缺陷检测与裂缝像素级分割系统。项目包含两部分能力：

1. **视觉大模型巡检**：上传道路图片，调用 Qwen 视觉大模型输出缺陷类型、严重程度、位置、修复建议等结构化结果，并自动生成工单。
2. **裂缝像素级分割（课程作业模块）**：使用 DeepLabV3+ 与 SegFormer-B0 两个真实训练的分割模型，输出裂缝掩码，进一步量化长度、宽度、面积占比，并按 JTG 5210 思路自动分级。

## 功能

- 用户登录、角色权限（巡检员 / 管理员）
- 道路点位管理、道路地图
- 图片上传 → 视觉大模型分析 → 巡检记录
- 缺陷严重程度规则化判定（坑洞按直径、裂缝按宽度、车辙按深度）
- 工单自动生成与处理流程
- 裂缝像素级分割：预处理好坏对比、双模型对比、掩码叠加
- 裂缝量化：连通域计数、骨架长度、距离变换宽度、面积占比
- 自动分级与自动工单
- 数据仪表盘与实验指标图表

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | FastAPI、SQLAlchemy、SQLite、JWT |
| 前端 | Vue 3、Vite、Element Plus、Pinia、ECharts |
| 视觉大模型 | 阿里云百炼 DashScope，Qwen 视觉模型 |
| 分割模型 | PyTorch、segmentation-models-pytorch、DeepLabV3+、SegFormer-B0 |
| 图像处理 | OpenCV、scikit-image、SciPy、Albumentations |
| 部署 | ONNX / ONNX Runtime（CPU 推理测速） |

## 目录结构

```
daolu_system/
├── backend/                     FastAPI 后端
│   ├── routers/                 认证、巡检、工单、道路、仪表盘、分割接口
│   ├── services/                视觉大模型服务、分割推理服务、定级规则
│   ├── models/                  SQLAlchemy 数据模型
│   ├── seed.py                  种子数据
│   └── main.py                  应用入口
├── frontend/                    Vue 3 前端
│   └── src/
│       ├── views/               仪表盘、巡检、工单、道路、裂缝分割
│       ├── components/          AI 结果卡片
│       └── api/                 接口封装
└── segmentation/                裂缝分割算法模块（课程作业重点）
    ├── prepare_data.py          数据整理与划分
    ├── preprocessing.py         CLAHE / Retinex / 双边滤波
    ├── dataset.py               数据集与增强
    ├── seg_models.py            DeepLabV3+ / SegFormer-B0 构建
    ├── train.py                 训练脚本
    ├── evaluate.py              指标、阈值扫描、可视化
    ├── postprocess.py           阈值 + 形态学后处理
    ├── quantification.py        长度/宽度/面积量化与分级
    ├── baseline_otsu.py         传统 Otsu 基线
    ├── analyze_images.py        图像特征分析
    ├── export_onnx.py           ONNX 导出与 CPU 测速
    ├── summarize_experiments.py 实验汇总
    ├── plot_results.py          训练曲线与消融图
    ├── weights/                 两套训练权重
    └── 实验报告.md              课程作业实验报告
```

## 快速开始

### 1. 后端

```powershell
cd backend
# 建议使用已安装 PyTorch 的 Python 环境
pip install -r requirements.txt

# 视觉大模型需要 DashScope Key，请不要把 Key 写入代码
$env:DASHSCOPE_API_KEY = "你的百炼 API Key"

python -m uvicorn main:yingyong --host 0.0.0.0 --port 8001
```

首次启动会自动创建 SQLite 数据库并注入种子数据。

演示账号：

| 账号 | 密码 | 角色 |
| --- | --- | --- |
| admin | admin123 | 管理员 |
| user1 | user123 | 巡检员 |

### 2. 前端

```powershell
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`，使用演示账号登录。

### 3. 裂缝分割模块

数据集不进入仓库，需要先准备数据（DeepCrack 与 CFD）：

```powershell
cd segmentation
pip install -r requirements.txt
python prepare_data.py
```

训练两个主模型：

```powershell
python train.py --model deeplabv3plus_mobilenetv2 --preprocess full --loss bce_dice --epochs 40 --weights-name deeplabv3plus_mobilenetv2_best.pth
python train.py --model segformer_b0 --preprocess full --loss bce_dice --epochs 40 --weights-name segformer_b0_best.pth
```

评估：

```powershell
python evaluate.py --checkpoint weights/deeplabv3plus_mobilenetv2_best.pth --data data/processed/deepcrack/test --output runs/eval_deeplab_deepcrack
python evaluate.py --checkpoint weights/segformer_b0_best.pth --data data/processed/deepcrack/test --output runs/eval_segformer_deepcrack
```

## 实验结果（DeepCrack 测试集）

| 模型 | IoU | Dice | Precision | Recall | 边界 IoU | 参数量 | GPU 单图 | ONNX CPU 单图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepLabV3+ (MobileNetV2) | 0.6785 | 0.7990 | 0.8776 | 0.7594 | 0.5408 | 4.38M | 7.0ms | 23.12ms |
| SegFormer-B0 | 0.6935 | 0.8118 | 0.8683 | 0.7836 | 0.5424 | 3.71M | 21.7ms | 61.79ms |

跨数据集（CFD）测试：

| 模型 | IoU | Dice |
| --- | --- | --- |
| DeepLabV3+ | 0.3786 | 0.5320 |
| SegFormer-B0 | 0.4249 | 0.5856 |

更完整的实验数据、消融分析与答辩要点见 [segmentation/实验报告.md](segmentation/实验报告.md)。

## 说明

- 仓库包含两套训练权重（`segmentation/weights/`），可直接运行分割推理。
- 数据集、上传图片、SQLite 数据库和训练中间产物已通过 `.gitignore` 排除。
- 视觉大模型 API Key 通过环境变量 `DASHSCOPE_API_KEY` 读取，仓库中不包含真实 Key。
- 课程作业要求的前端展示沿用现有 FastAPI + Vue 技术栈，未单独引入 Flask。
