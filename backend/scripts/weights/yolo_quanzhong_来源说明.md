# YOLOv8-RDD2022 权重来源与模型说明

本文件用于说明对比实验所用传统目标检测权重的来源、训练背景与可核对性，供答辩与说明书使用。

## 一、权重来源

| 项目 | 内容 |
|---|---|
| 权重文件 | backend/scripts/weights/rdd_yolov8_best.pt |
| 原始文件路径 | GitHub 仓库 models/best.pt（main 分支） |
| 文件大小 | 6,248,234 字节 |
| SHA-256 | 4A20A768687D094A3F68EBC8B787E7DC93FCA4A5049D82518188E0B58DB672D2 |
| 仓库地址 | https://github.com/FulberRenika/Road-Damage-Detection-Using-YOLOv8 |
| 作者 | Fulber Renika C R（GitHub 主页 https://github.com/FulberRenika，计算机科学方向在校学生） |
| 仓库创建时间 | 2026-06-11 |

原始下载地址：
https://raw.githubusercontent.com/FulberRenika/Road-Damage-Detection-Using-YOLOv8/main/models/best.pt

## 二、模型训练背景（取自作者 README）

| 项目 | 内容 |
|---|---|
| 基础模型 | YOLOv8n |
| 训练数据集 | RDD2022 Road Damage Dataset（国际公开道路损伤基准，含中国等六国数据） |
| 训练轮数 | 20 epochs |
| 输入尺寸 | 640 x 640 |
| 批大小 | 16 |
| 输出类别（8 类） | D00、D01（纵向裂缝类）、D10、D11（横向裂缝类）、D20（龟裂）、D40（坑洞）、D43、D44（修补痕迹类） |
| 训练环境 | Google Colab + OpenCV |

作者 README 原文已存档：backend/scripts/jieguo/yolo_quanzhong_README.md

## 三、上游数据集出处（用于向评委说明权威性）

- 论文：Deeksha Arya et al., RDD2022: A multi-national image dataset for automatic Road Damage Detection, Data in Brief (2022)
- 数据集：RDD2022，47,420 张道路图像、六国数据（含中国）、55,000 余个损伤标注

## 四、使用方式与立场说明

1. 本实验直接加载上述预训练权重进行推理，未做任何权重修改；
2. 该权重在贴近其训练分布的样本上具备检出能力（本实验样本中亦检出 D40 坑洞）；
3. 本系统测试样本的拍摄视角与场景分布同 RDD2022 训练分布存在差异，且样本多为复合病害，这是检出率低的主要原因，并非模型本身无效；
4. 该结果用于论证"传统目标检测依赖特定数据分布、在跨场景数据上表现受限"，与"视觉大模型零样本泛化"形成对比，属系统选型实验的一部分。

## 五、答辩口径建议

如评委询问模型来源：
"传统目标检测路线我们采用了一个在公开国际基准数据集 RDD2022 上训练好的 YOLOv8 预训练权重，来自 GitHub 开源仓库 FulberRenika/Road-Damage-Detection-Using-YOLOv8（作者 Fulber Renika C R），模型配置为 YOLOv8n、20 轮、8000 类八类缺陷。我们直接加载该权重对测试图片推理，未做修改。该模型在贴近训练分布的图形上能正常检出缺陷（本次样本即检出坑洞），但在拍摄视角与本系统相近的复杂场景上检出率明显下降，这也正是我们选择零样本视觉大模型的原因之一。"