# -*- coding: utf-8 -*-
"""
缺陷严重程度规则化判定引擎

设计目标：严重程度不直接采信大模型的猜测，而是由规则引擎按行业病害阈值判定，
大模型输出仅作为兜底。规则参考《公路技术状况评定标准》(JTG 5210-2018)
关于路面病害分级的思路，结合可获取的量化信息：

  1. 解析模型输出的物理尺寸文本（如"直径约30厘米"、"宽度约5毫米"），
     按缺陷类型对应的维度阈值分级：坑洞按直径、裂缝按宽度、车辙按深度；
  2. 无尺寸文本时，用缺陷归一化边界框的面积占比近似估算；
  3. 两者都不可用时，回退使用模型直接输出的严重程度。
"""

import re
import logging

rizhi = logging.getLogger(__name__)

# 等级排序（用于取多个缺陷中的最严重者）
DINGJI_SHUNXU = {'无': 0, '轻微': 1, '中等': 2, '严重': 3}
DINGJI_JI = set(DINGJI_SHUNXU.keys())

# 坑洞：按直径分级（毫米）
KENGDONG_FENJI = [(150, '轻微'), (300, '中等'), (float('inf'), '严重')]
# 裂缝：按宽度分级（毫米）
LIEFENG_FENJI = [(3, '轻微'), (10, '中等'), (float('inf'), '严重')]
# 车辙：按深度分级（毫米）
CHEZHE_FENJI = [(15, '轻微'), (25, '中等'), (float('inf'), '严重')]
# 面积占比分级（龟裂、松散、修补痕迹等按缺陷面积相对图像占比近似）
MIANJI_FENJI = [(0.05, '轻微'), (0.15, '中等'), (float('inf'), '严重')]

# 尺寸单位换算为毫米
DANWEI_HAOMI = {
    'mm': 1,
    '毫米': 1,
    'cm': 10,
    '厘米': 10,
    'm': 1000,
    '米': 1000,
}

# 面积单位换算为平方米
DANWEI_PINGFANGMI = {
    '平方米': 1,
    '㎡': 1,
    'm2': 1,
    'm²': 1,
}

# 类型对应的判定维度与描述
LEIXING_DIMENSIONS = {
    '坑洞': ('kengdong', '直径'),
    '裂缝': ('liefeng', '宽度'),
    '车辙': ('chezhe', '深度'),
}


def _tiqu_chicun(wenben):
    """从尺寸描述文本提取 (数值, 单位, 毫米值 或 None)"""
    if not wenben:
        return None
    pipei = re.search(r'(\d+(?:\.\d+)?)\s*(mm|毫米|cm|厘米|米|m|平方米|㎡|m\s?2|m²)', wenben, re.IGNORECASE)
    if not pipei:
        return None
    shu = float(pipei.group(1))
    danwei = pipei.group(2).lower().replace(' ', '')
    if danwei in DANWEI_HAOMI:
        return (shu, danwei, shu * DANWEI_HAOMI[danwei])
    return (shu, danwei, None)


def _mianji_zhanyi(jiankuang):
    """依据归一化边界框计算缺陷面积占图像的比例"""
    if not jiankuang or len(jiankuang) != 4:
        return None
    kuan = max(0.0, jiankuang[2] - jiankuang[0])
    gao = max(0.0, jiankuang[3] - jiankuang[1])
    return kuan * gao


def _shuang_haomi_fenji(hao_mi, fenji):
    """按毫米阈值区间返回等级"""
    for menxian, dengji in fenji:
        if hao_mi < menxian:
            return dengji
    return '严重'


def _quan_fenji(zhanyibi, fenji):
    """按占比阈值区间返回等级"""
    for menxian, dengji in fenji:
        if zhanyibi < menxian:
            return dengji
    return '严重'


def _xiao_yansou(moxing_jieguo):
    """模型兜底等级，非法值归一为 中等"""
    if moxing_jieguo in DINGJI_JI:
        return moxing_jieguo
    return '中等'


def panduan_yanzhong(queshi_leixing, chicun_wenben, jiankuang, moxing_jieguo):
    """
    规则化判定单个缺陷的严重程度

    参数:
        queshi_leixing: 缺陷类型（坑洞/裂缝/车辙/龟裂/松散/修补痕迹等）
        chicun_wenben: 模型输出的尺寸估计文本，如"直径约30厘米"
        jiankuang: 归一化边界框 [x1, y1, x2, y2]
        moxing_jieguo: 模型直接输出的严重程度（兜底）

    返回:
        (等级, 来源, 判定依据)  来源为 guize 或 moxing
    """
    leixing = queshi_leixing or ''
    if leixing in ('无', '无法识别', ''):
        return ('无', 'moxing', '无缺陷或无法识别')

    # 1. 优先解析物理尺寸文本
    tiqu = _tiqu_chicun(chicun_wenben)
    weidu = leixing in LEIXING_DIMENSIONS
    if tiqu and tiqu[2] is not None:
        shu, danwei, hao_mi = tiqu
        if leixing == '坑洞':
            dengji = _shuang_haomi_fenji(hao_mi, KENGDONG_FENJI)
            return (dengji, 'guize', f'坑洞{chicun_wenben}，按直径阈值分级')
        if leixing == '裂缝':
            dengji = _shuang_haomi_fenji(hao_mi, LIEFENG_FENJI)
            return (dengji, 'guize', f'裂缝{chicun_wenben}，按宽度阈值分级')
        if leixing == '车辙':
            dengji = _shuang_haomi_fenji(hao_mi, CHEZHE_FENJI)
            return (dengji, 'guize', f'车辙{chicun_wenben}，按深度阈值分级')
        # 其他类型（龟裂/松散/修补痕迹）：有长度尺寸时结合边界框面积占比分级
        mianji = _mianji_zhanyi(jiankuang)
        if mianji is not None and mianji > 0:
            dengji = _quan_fenji(mianji, MIANJI_FENJI)
            return (dengji, 'guize', f'{leixing}面积占比{mianji * 100:.1f}%，按面积阈值分级')
        return (_xiao_yansou(moxing_jieguo), 'moxing', '尺寸不可作为分级维度，采用模型结果')

    # 2. 无可用物理尺寸：用边界框面积占比估算
    mianji = _mianji_zhanyi(jiankuang)
    if mianji is not None and mianji > 0:
        dengji = _quan_fenji(mianji, MIANJI_FENJI)
        return (dengji, 'guize', f'缺陷图像面积占比{mianji * 100:.1f}%，按面积阈值分级')

    # 3. 兜底：模型直接输出
    return (_xiao_yansou(moxing_jieguo), 'moxing', '缺少量化信息，采用模型结果')