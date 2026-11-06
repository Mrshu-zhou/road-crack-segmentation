# -*- coding: utf-8 -*-
"""
道路图片 AI 分析服务
使用 OpenAI SDK 调用 DashScope 视觉大模型，检测路面缺陷
"""

import os
import json
import base64
import re
import logging

from openai import OpenAI

from config import (
    DASHSCOPE_API_KEY, DASHSCOPE_JIEKOU_DIZHI, DASHSCOPE_MOXING, AI_CHAOSHI,
)

rizhi = logging.getLogger(__name__)

# System Prompt 文件路径
XITONG_TISHI_LUJING = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'prompts', 'system_prompt.txt'
)


def jiazai_xitong_tishi() -> str:
    """从 prompts/system_prompt.txt 加载系统提示词"""
    with open(XITONG_TISHI_LUJING, 'r', encoding='utf-8') as f:
        return f.read()


# ============================================================
# JSON 兜底默认值
# ============================================================
MOREN_JIEGUO = {
    "daolu_zhuangkuang": "无法识别",
    "queshi_leixing": "无法识别",
    "yansong_chengdu": "无法识别",
    "queshi_weizhi": "无法识别",
    "chuli_jianyi": "无法识别",
    "suo_xu_cailiao": "无法识别",
    "yingji_chengdu": "无法识别",
    "quexian_qingdan": [],
}

# 支持的图片格式
ZHICHI_GESHI = {".jpg", ".jpeg", ".png", ".webp"}

# 中文键名 → 拼音键名映射（模型可能返回中文键名）
ZIDUAN_YINGSHE = {
    "道路状况": "daolu_zhuangkuang",
    "缺陷类型": "queshi_leixing",
    "严重程度": "yansong_chengdu",
    "缺陷位置": "queshi_weizhi",
    "修复建议": "chuli_jianyi",
    "所需材料": "suo_xu_cailiao",
    "紧急程度": "yingji_chengdu",
    "缺陷清单": "quexian_qingdan",
}

# 缺陷清单条目内的中文键名 → 拼音键名映射
QINGDAN_ZIDUAN_YINGSHE = {
    "类型": "leixing",
    "位置": "weizhi",
    "边界框": "jiankuang",
    "尺寸估计": "chicun_gu_ji",
    "尺寸": "chicun_gu_ji",
}

# MIME 类型映射
MIME_DUIYING = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _tupian_zhuan_base64(tupian_lujing: str) -> str:
    """将图片文件转为 base64 data URL"""
    houzhui = os.path.splitext(tupian_lujing)[1].lower()
    if houzhui not in ZHICHI_GESHI:
        raise ValueError(f"不支持的图片格式：'{houzhui}'，仅支持 {', '.join(ZHICHI_GESHI)}")
    if not os.path.isfile(tupian_lujing):
        raise FileNotFoundError(f"图片文件不存在：{tupian_lujing}")

    mime_leixing = MIME_DUIYING[houzhui]
    with open(tupian_lujing, "rb") as f:
        bianma_shuju = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_leixing};base64,{bianma_shuju}"


def _jiexi_json(yuanshi_neirong: str):
    """从模型返回内容中提取 JSON，先 json.loads，失败则正则提取"""
    try:
        return json.loads(yuanshi_neirong)
    except json.JSONDecodeError:
        pass

    # 正则提取 {...} 兜底
    pipei_jieguo = re.search(r"\{[\s\S]*\}", yuanshi_neirong)
    if pipei_jieguo:
        try:
            return json.loads(pipei_jieguo.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _zhengli_quexian_qingdan(qingdan):
    """整理缺陷清单：字典转数组、映射中文键名、校验归一化边界框"""
    if qingdan is None:
        return []
    if isinstance(qingdan, (dict, str)):
        if isinstance(qingdan, str):
            # 模型可能把数组序列化成字符串，尝试解析
            yingjie = _jiexi_json(qingdan)
            qingdan = yingjie if isinstance(yingjie, list) else []
        else:
            qingdan = [qingdan]
    if not isinstance(qingdan, list):
        return []

    jieguo = []
    for tiao_mu in qingdan:
        if not isinstance(tiao_mu, dict):
            continue
        # 中文键名映射到拼音键名
        gui_fan = {jian: zhi for jian, zhi in tiao_mu.items()}
        for zhongwen, pinyin in QINGDAN_ZIDUAN_YINGSHE.items():
            if zhongwen in gui_fan:
                gui_fan[pinyin] = gui_fan[zhongwen]

        # 校验归一化边界框：4 个 0~1 之间的数值
        jiankuang = gui_fan.get("jiankuang")
        if (
            isinstance(jiankuang, list)
            and len(jiankuang) == 4
            and all(isinstance(s, (int, float)) for s in jiankuang)
        ):
            jiankuang = [max(0.0, min(1.0, float(s))) for s in jiankuang]
            # 过滤过小噪声框（面积占比低于十万分之一，近似一个点）
            kuan = max(0.0, jiankuang[2] - jiankuang[0])
            gao = max(0.0, jiankuang[3] - jiankuang[1])
            if kuan * gao < 0.0001:
                jiankuang = None
        else:
            jiankuang = None

        xin_tiao = {
            "leixing": gui_fan.get("leixing", ""),
            "weizhi": gui_fan.get("weizhi", ""),
            "chicun_gu_ji": gui_fan.get("chicun_gu_ji", ""),
            "jiankuang": jiankuang,
        }
        if xin_tiao["leixing"]:
            jieguo.append(xin_tiao)
    return jieguo


def _tianchong_morenquedu(jiexi_jieguo: dict) -> dict:
    """将模型返回的键名映射为拼音键名，填充缺失的键，处理数组字段"""
    # 1. 中文键名 → 拼音键名
    yingshe_jieguo = {}
    for jian, zhi in jiexi_jieguo.items():
        if jian in ZIDUAN_YINGSHE:
            yingshe_jieguo[ZIDUAN_YINGSHE[jian]] = zhi
        else:
            yingshe_jieguo[jian] = zhi

    # 2. 数组字段转字符串（如 所需材料 用顿号拼接）
    if "suo_xu_cailiao" in yingshe_jieguo and isinstance(yingshe_jieguo["suo_xu_cailiao"], list):
        yingshe_jieguo["suo_xu_cailiao"] = "、".join(yingshe_jieguo["suo_xu_cailiao"])

    # 3. 填充缺失字段
    wan_zheng_jieguo = {}
    for ziduan, moren_zhi in MOREN_JIEGUO.items():
        if ziduan == "quexian_qingdan":
            # 缺陷清单单独处理：校验结构并保证为数组
            wan_zheng_jieguo[ziduan] = _zhengli_quexian_qingdan(yingshe_jieguo.get(ziduan))
        else:
            wan_zheng_jieguo[ziduan] = yingshe_jieguo.get(ziduan, moren_zhi)
    return wan_zheng_jieguo


def fenxi_daolu_tupian(tupian_lujing: str) -> dict:
    """
    分析道路图片，检测路面缺陷

    参数:
        tupian_lujing (str): 图片文件路径

    返回:
        dict: 包含分析结果的 JSON 字典，字段为拼音键名
    """
    # 1. 图片编码为 base64 data URL
    tupian_url = _tupian_zhuan_base64(tupian_lujing)

    # 2. 加载系统提示词
    xitong_tishi = jiazai_xitong_tishi()

    # 3. 构造 OpenAI 客户端（指向 DashScope 兼容接口）
    # 单次请求超时 60 秒（AI_CHAOSHI），最多重试 2 次，总预算约 3 分钟内
    kehuduan = OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_JIEKOU_DIZHI,
        timeout=AI_CHAOSHI,
        max_retries=2,
    )

    # 4. 调用视觉模型
    try:
        xiangying = kehuduan.chat.completions.create(
            model=DASHSCOPE_MOXING,
            messages=[
                {"role": "system", "content": xitong_tishi},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": tupian_url},
                        },
                        {
                            "type": "text",
                            "text": "请分析这张道路图片，返回 JSON 格式结果。",
                        },
                    ],
                },
            ],
            max_tokens=1024,
        )
    except Exception as e:
        rizhi.error(f"AI API 调用失败（{type(e).__name__}）: {e}")
        return {
            **MOREN_JIEGUO,
            "daolu_zhuangkuang": f"API 调用失败：{str(e)}",
            "queshi_leixing": "API 错误",
        }

    # 5. 提取返回内容
    yuanshi_neirong = xiangying.choices[0].message.content

    # 6. 解析 JSON
    jiexi_jieguo = _jiexi_json(yuanshi_neirong)
    if jiexi_jieguo is None:
        return {
            **MOREN_JIEGUO,
            "daolu_zhuangkuang": f"JSON 解析失败，原始返回：{yuanshi_neirong[:500]}",
            "queshi_leixing": "解析错误",
        }

    # 7. 填充默认值并返回
    return _tianchong_morenquedu(jiexi_jieguo)
