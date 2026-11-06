# -*- coding: utf-8 -*-
"""
模型对比实验脚本（答辩用）
对比传统目标检测（YOLOv8）与视觉大模型（Qwen3.6-Plus）在道路缺陷识别上的效果。

运行前提：
1. 后端依赖已安装（openai、config 等），见 backend/requirements.txt
2. 可选：安装 ultralytics（用于 YOLOv8 推理）：pip install ultralytics
3. --biaozhu 参数：可选的人工标注 JSON，格式：
   {"图片文件名": "坑洞"} 或 {"图片文件名": ["坑洞", "裂缝"]}

用法示例：
  python scripts/duibi_shiyan.py --tupian ../uploads --biaozhu biaozhu.json
  python scripts/duibi_shiyan.py --tupian ../uploads   # 不提供标注时只对比耗时与输出能力

产出：
  scripts/jieguo/ 目录下生成
  - vl_jieguo.json      视觉大模型逐图结果
  - yolo_jieguo.json    YOLOv8 推断结果
  - duibi_baogao.md     对比实验报告（可直接截图进 PPT）
"""

import os
import sys
import json
import time
import argparse
import logging

# 将 backend 目录加入模块搜索路径，便于复用 ai_service 与 config
BACKEND_MULU = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_MULU not in sys.path:
    sys.path.insert(0, BACKEND_MULU)

# 注意：ai_service 需 openai，在 yolo 环境缺失。将 import 放在函数内部，
# 使脚本在只装 ultralytics 的环境也能跑 YOLO 部分（VL 部分给出跳过提示）。

rizhi = logging.getLogger(__name__)

ZHICHI_GESHI = {'.jpg', '.jpeg', '.png', '.webp'}

# 缺陷类型全集（用于匹配准确率计算）
QUESHI_LEIXING_JI = {'坑洞', '裂缝', '龟裂', '车辙', '松散', '修补痕迹', '无'}


def jiazai_biaozhu(biaozhu_lujing):
    """加载人工标注 JSON，返回 文件名 -> 类型集合 的字典"""
    if not biaozhu_lujing or not os.path.isfile(biaozhu_lujing):
        return {}
    with open(biaozhu_lujing, 'r', encoding='utf-8') as f:
        yuan_shuju = json.load(f)
    jieguo = {}
    for wenjianming, leixing in yuan_shuju.items():
        if isinstance(leixing, list):
            jieguo[wenjianming] = set(leixing)
        else:
            jieguo[wenjianming] = {leixing}
    return jieguo


def souji_tupian(tupian_mulu):
    """收集目录下的图片文件列表"""
    wenjian_liebiao = []
    if not os.path.isdir(tupian_mulu):
        rizhi.error(f'图片目录不存在: {tupian_mulu}')
        return wenjian_liebiao
    for wenjianming in sorted(os.listdir(tupian_mulu)):
        kuozhanming = os.path.splitext(wenjianming)[1].lower()
        if kuozhanming in ZHICHI_GESHI:
            wenjian_liebiao.append(os.path.join(tupian_mulu, wenjianming))
    return wenjian_liebiao


def shibie_zhonglei(vl_jieguo):
    """从 VL 分析结果中取类型集合"""
    leixing = vl_jieguo.get('queshi_leixing', '')
    if leixing and leixing not in ('无', '无法识别', 'API 错误', '解析错误'):
        return {leixing}
    return set()


def yunxing_vl_shiyan(wenjian_liebiao, biaozhu):
    """运行视觉大模型实验，返回逐图结果与统计"""
    try:
        from services.ai_service import fenxi_daolu_tupian
    except ImportError as e:
        rizhi.error(f'缺少 openai 依赖，跳过视觉大模型实验（可在 ruanzhu 环境运行）: {e}')
        return {
            'jieguo_liebiao': [],
            'tongji': {'zongshu': 0, 'pingjun_haoshi_miao': 0, 'tiaoguo_yuanyin': '缺少 openai（VL 部分需在 ruanzhu 环境运行）'},
        }
    rizhi.info(f'开始视觉大模型实验，共 {len(wenjian_liebiao)} 张图片')
    jieguo_liebiao = []
    zong_haoshi = 0.0
    pipei_shu = 0
    youxiaoshuju_shu = 0
    for lujing in wenjian_liebiao:
        wenjianming = os.path.basename(lujing)
        kaishi = time.time()
        try:
            jieguo = fenxi_daolu_tupian(lujing)
            haoshi = time.time() - kaishi
            zong_haoshi += haoshi
            shibie = shibie_zhonglei(jieguo)
            this_zhang = {
                'wenjianming': wenjianming,
                'haoshi_miao': round(haoshi, 2),
                'queshi_leixing': jieguo.get('queshi_leixing', ''),
                'yansong_chengdu': jieguo.get('yansong_chengdu', ''),
                'shibie_zhonglei': sorted(shibie),
                'quexian_qingdan': jieguo.get('quexian_qingdan', []),
                'cuowu': '',
            }
            # 统计类型匹配准确率：识别集合与标注集合一致才算命中
            if wenjianming in biaozhu:
                youxiaoshuju_shu += 1
                biaozhu_leixing = biaozhu[wenjianming]
                # "无"标注表示该图无缺陷
                biaozhu_leixing = biaozhu_leixing - {'无'} if biaozhu_leixing else set()
                if shibie == biaozhu_leixing:
                    pipei_shu += 1
                    this_zhang['pipei'] = True
                else:
                    this_zhang['pipei'] = False
                    this_zhang['biaozhu_leixing'] = sorted(biaozhu_leixing)
            jieguo_liebiao.append(this_zhang)
        except Exception as e:
            rizhi.exception(f'VL 分析失败: {lujing}')
            jieguo_liebiao.append({
                'wenjianming': wenjianming,
                'haoshi_miao': round(time.time() - kaishi, 2),
                'queshi_leixing': '',
                'yansong_chengdu': '',
                'shibie_zhonglei': [],
                'quexian_qingdan': [],
                'cuowu': str(e),
            })

    tongji = {
        'zongshu': len(wenjian_liebiao),
        'pingjun_haoshi_miao': round(zong_haoshi / len(wenjian_liebiao), 2) if wenjian_liebiao else 0,
        'tonglei_youtube': 0,
    }
    # 有标注时的准确率
    zhengquelv = None
    if youxiaoshuju_shu:
        zhengquelv = round(pipei_shu / youxiaoshuju_shu * 100, 2)
    tongji['youbiaozhu_shu'] = youxiaoshuju_shu
    tongji['pipei_shu'] = pipei_shu
    tongji['zhengquelv'] = zhengquelv
    return {'jieguo_liebiao': jieguo_liebiao, 'tongji': tongji}


def yunxing_yolo_shiyan(wenjian_liebiao, yolo_quanzhong='yolov8n.pt'):
    """运行 YOLOv8 实验，返回逐图结果与统计

    参数:
        yolo_quanzhong: 权重文件路径。默认 yolov8n.pt（COCO 通用预训练）；
            可传 RDD 上微调好的权重（如 scripts/weights/rdd_yolov8_best.pt）。
    说明：COCO 预训练 YOLOv8 不含道路缺陷类别（坑洞/裂缝等），
    该实验用于展示传统方案两方面的特点：
    1. 通用预训练模型无法识别缺陷类别，必须用道路缺陷数据（如 RDD2020）微调；
    2. 使用微调权重（rdd_*.pt）即可直接检出纵向裂缝/横向裂缝/龟裂/坑洞等类别。
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        rizhi.warning('ultralytics 未安装，跳过 YOLOv8 实验。安装方式: pip install ultralytics')
        return {
            'jieguo_liebiao': [],
            'tongji': {'zongshu': 0, 'pingjun_haoshi_miao': 0, 'tiaoguo_yuanyin': 'ultralytics 未安装'},
        }

    try:
        moxing = YOLO(yolo_quanzhong)
    except Exception as e:
        return {
            'jieguo_liebiao': [],
            'tongji': {'zongshu': 0, 'pingjun_haoshi_miao': 0, 'tiaoguo_yuanyin': f'权重加载失败: {e}'},
        }

    jieguo_liebiao = []
    zong_haoshi = 0.0
    for lujing in wenjian_liebiao:
        wenjianming = os.path.basename(lujing)
        kaishi = time.time()
        try:
            jieguo = moxing.predict(lujing, verbose=False)
            haoshi = time.time() - kaishi
            zong_haoshi += haoshi
            jianchu_lei = []
            for r in jieguo:
                for m in r.boxes:
                    jianchu_lei.append(moxing.names[int(m.cls.item())])
            jieguo_liebiao.append({
                'wenjianming': wenjianming,
                'haoshi_miao': round(haoshi, 2),
                'jianchu_lei': jianchu_lei[:10],
                'cuowu': '',
            })
        except Exception as e:
            rizhi.exception(f'YOLO 推理失败: {lujing}')
            jieguo_liebiao.append({
                'wenjianming': wenjianming,
                'haoshi_miao': round(time.time() - kaishi, 2),
                'jianchu_lei': [],
                'cuowu': str(e),
            })

    tongji = {
        'zongshu': len(wenjian_liebiao),
        'pingjun_haoshi_miao': round(zong_haoshi / len(wenjian_liebiao), 2) if wenjian_liebiao else 0,
        'bei_zhu_ming': 'COCO 预训练权重，不含道路缺陷类别',
    }
    return {'jieguo_liebiao': jieguo_liebiao, 'tongji': tongji}


def shengcheng_baogao(vl_shuju, yolo_shuju, tupian_shuliang, yolo_quanzhong='yolov8n.pt'):
    """生成 Markdown 对比报告"""
    vl_tongji = vl_shuju['tongji']
    yolo_tongji = yolo_shuju['tongji']
    hang = []
    hang.append('# 道路缺陷识别：视觉大模型 与 YOLOv8 对比实验报告')
    hang.append('')
    hang.append(f'测试图片数量：{tupian_shuliang} 张')
    hang.append(f'YOLOv8 使用权重：{os.path.basename(str(yolo_quanzhong))}')
    hang.append('')
    hang.append('## 对比总览')
    hang.append('')
    hang.append('| 维度 | 视觉大模型 (Qwen3.6-Plus) | YOLOv8 |')
    hang.append('| --- | --- | --- |')
    shi_fou_rdd = 'rdd' in os.path.basename(str(yolo_quanzhong)).lower()
    xunlian_xu = '是（RDD2020 等微调）' if shi_fou_rdd else '是（COCO 通用权重不含缺陷类）'
    shibie_neng = '能（纵向/横向裂缝、龟裂、坑洞）' if shi_fou_rdd else '不能（仅 COCO 类别）'
    hang.append(f'| 是否需要训练标注 | 否（零样本） | {xunlian_xu} |')
    hang.append(f'| 单图平均耗时 | {vl_tongji.get("pingjun_haoshi_miao", "-")} 秒 | {yolo_tongji.get("pingjun_haoshi_miao", "-")} 秒 |')
    hang.append(f'| 能否直接识别道路缺陷 | 能（坑洞/裂缝/龟裂/车辙/松散等） | {shibie_neng} |')
    hang.append(f'| 输出信息 | 类型、严重度、位置、修复建议、材料、检测框、尺寸 | 仅目标框与类别 |')
    zhengquelv = vl_tongji.get('zhengquelv')
    if zhengquelv is not None:
        hang.append(f'| 类型匹配率（有标注样本） | {zhengquelv}% | 未统计 |')
    else:
        hang.append(f'| 类型匹配率 | 未提供人工标注，未计算 | 未提供人工标注，未计算 |')
    hang.append('')
    hang.append('## 结论')
    hang.append('')
    hang.append('传统目标检测（以 YOLOv8 为例）在道路缺陷场景下的主要限制：')
    hang.append('1. 缺陷类别多样（坑洞、裂缝、龟裂、车辙、松散、修补痕迹等），标注数据获取成本高、周期长；')
    if shi_fou_rdd:
        hang.append('2. 使用 RDD 微调权重虽能检出已知缺陷类别，但难以泛化到未训练过的新型缺陷；')
    else:
        hang.append('2. 通用预训练模型不含道路缺陷类别，直接推理无法给出缺陷类型；')
    hang.append('3. 输出仅为目标框和类别，缺少严重程度、修复建议、所需材料等养护决策需要的深度信息。')
    hang.append('')
    hang.append('视觉大模型方案：零样本识别多类缺陷，一次推理同时输出结构化七维信息（含检测框与尺寸），')
    hang.append('更适合快速落地与泛化到新型缺陷。')
    hang.append('')
    hang.append('## 附录：逐图明细')
    hang.append('')
    hang.append('### 视觉大模型')
    hang.append('')
    hang.append('| 图片 | 耗时(秒) | 检出类型 | 严重度 |')
    hang.append('| --- | --- | --- | --- |')
    for item in vl_shuju['jieguo_liebiao']:
        hang.append(f"| {item['wenjianming']} | {item['haoshi_miao']} | {item['queshi_leixing'] or item.get('cuowu', '-')} | {item['yansong_chengdu']} |")
    hang.append('')
    hang.append('### YOLOv8')
    hang.append('')
    hang.append('| 图片 | 耗时(秒) | 检出类别 |')
    hang.append('| --- | --- | --- |')
    for item in yolo_shuju['jieguo_liebiao']:
        hang.append(f"| {item['wenjianming']} | {item['haoshi_miao']} | {', '.join(item['jianchu_lei']) or item.get('cuowu', '-')} |")
    hang.append('')
    return '\n'.join(hang)


def zhunbei_shuchu_mulu():
    """准备输出目录"""
    jieguo_mulu = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jieguo')
    os.makedirs(jieguo_mulu, exist_ok=True)
    return jieguo_mulu


def baocun_json(lujing, shuju):
    with open(lujing, 'w', encoding='utf-8') as f:
        json.dump(shuju, f, ensure_ascii=False, indent=2)


def main():
    jiexi = argparse.ArgumentParser(description='模型对比实验：YOLOv8 vs 视觉大模型')
    jiexi.add_argument('--tupian', required=True, help='测试图片目录路径')
    jiexi.add_argument('--biaozhu', default='', help='人工标注 JSON 文件路径（可选）')
    jiexi.add_argument('--yolo_quanzhong', default='yolov8n.pt',
                       help='YOLO 权重路径，默认 yolov8n.pt（COCO 通用预训练）；'
                            '可传 scripts/weights/ 下的 RDD 微调权重')
    canshu = jiexi.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    rizhi.info(f'收集图片目录: {canshu.tupian}')
    wenjian_liebiao = souji_tupian(canshu.tupian)
    if not wenjian_liebiao:
        rizhi.error('目录下没有可用图片，结束')
        return

    biaozhu = jiazai_biaozhu(canshu.biaozhu)
    if biaozhu:
        rizhi.info(f'加载人工标注 {len(biaozhu)} 条')

    shuchu_mulu = zhunbei_shuchu_mulu()

    # 1. 视觉大模型实验
    rizhi.info('正在运行视觉大模型实验（每张图片调用真实 API，耗时约 15 秒左右）...')
    vl_shuju = yunxing_vl_shiyan(wenjian_liebiao, biaozhu)
    baocun_json(os.path.join(shuchu_mulu, 'vl_jieguo.json'), vl_shuju)

    # 2. YOLOv8 实验
    rizhi.info(f'正在运行 YOLOv8 实验（权重: {canshu.yolo_quanzhong}）...')
    yolo_shuju = yunxing_yolo_shiyan(wenjian_liebiao, canshu.yolo_quanzhong)
    baocun_json(os.path.join(shuchu_mulu, 'yolo_jieguo.json'), yolo_shuju)

    # 3. 生成报告
    baogao = shengcheng_baogao(vl_shuju, yolo_shuju, len(wenjian_liebiao), canshu.yolo_quanzhong)
    baogao_lujing = os.path.join(shuchu_mulu, 'duibi_baogao.md')
    with open(baogao_lujing, 'w', encoding='utf-8') as f:
        f.write(baogao)
    rizhi.info(f'对比实验完成，报告已生成: {baogao_lujing}')


if __name__ == '__main__':
    main()