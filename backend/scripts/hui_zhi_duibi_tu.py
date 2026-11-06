# -*- coding: utf-8 -*-
"""生成模型对比图表（评委用）：检出能力与单图耗时对比"""
import os
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

JIEGUO_MULU = os.path.dirname(os.path.abspath(__file__))

# 加载两次实验的结果
vl_shuju = json.load(open(os.path.join(JIEGUO_MULU, 'jieguo', 'vl_jieguo.json'), encoding='utf-8'))
yolo_shuju = json.load(open(os.path.join(JIEGUO_MULU, 'jieguo', 'rdd_yolo_13zhang.json'), encoding='utf-8'))

vl_liebiao = vl_shuju['jieguo_liebiao']
yolo_liebiao = yolo_shuju['jieguo_liebiao']
zongshu = len(vl_liebiao)

# VL：识别到缺陷的图像数（缺陷类型非"无"）
vl_you_quexian = sum(1 for x in vl_liebiao if x.get('queshi_leixing') not in ('无', '无法识别', 'API 错误', '解析错误', ''))
# YOLO：检出框的图像数
yolo_you_quexian = sum(1 for x in yolo_liebiao if x.get('jianchu_lei'))
wu_quexian = zongshu - vl_you_quexian

# 单图平均耗时
vl_pingjun = vl_shuju['tongji'].get('pingjun_haoshi_miao', 0)
yolo_pingjun = yolo_shuju['tongji'].get('pingjun_haoshi_miao', 0)

# 统一中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4), dpi=150)

# 左图：检出能力（横向条形，视觉大模型在上）
hang_biaoqian = ['视觉大模型\n(Qwen3.6-Plus)', '传统目标检测\n(YOLOv8-RDD2022)']
hang_weizhi = [1, 0]  # 视觉在上(y=1)，传统在下(y=0)
ax1.barh(hang_weizhi, [vl_you_quexian, yolo_you_quexian],
         color=['#409eff', '#e6a23c'], height=0.42)
ax1.set_yticks(hang_weizhi)
ax1.set_yticklabels(hang_biaoqian)
ax1.set_xlim(0, zongshu + 1)
ax1.set_xlabel('检出缺陷的图像数量（共 %d 张）' % zongshu)
ax1.set_title('缺陷检出能力对比', fontsize=13, fontweight='bold')
ax1.text(vl_you_quexian + 0.15, 1, f'{vl_you_quexian}/{zongshu}', va='center',
         color='#409eff', fontweight='bold')
ax1.text(yolo_you_quexian + 0.15, 0, f'{yolo_you_quexian}/{zongshu}', va='center',
         color='#b06000', fontweight='bold')

# 右图：单图平均耗时
ax2.bar(['视觉大模型\n(Qwen3.6-Plus)', '传统目标检测\n(YOLOv8-RDD2022)'],
        [vl_pingjun, yolo_pingjun], color=['#409eff', '#e6a23c'], width=0.42)
ax2.set_ylabel('单图平均耗时（秒）')
ax2.set_title('单图平均耗时对比', fontsize=13, fontweight='bold')
ax2.text(0, vl_pingjun + 1, f'{vl_pingjun:.1f}s', ha='center', color='#409eff', fontweight='bold')
ax2.text(1, yolo_pingjun + 1, f'{yolo_pingjun:.2f}s', ha='center', color='#b06000', fontweight='bold')

plt.tight_layout()
shuchu = os.path.join(JIEGUO_MULU, 'jieguo', 'duibi_tuxing.png')
plt.savefig(shuchu, bbox_inches='tight')
print('图表已保存:', shuchu)
print(f'VL 检出缺陷图 {vl_you_quexian}/{zongshu}，平均 {vl_pingjun:.1f}s；YOLO 检出缺陷图 {yolo_you_quexian}/{zongshu}，平均 {yolo_pingjun:.2f}s')