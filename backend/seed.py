# -*- coding: utf-8 -*-
"""
种子数据初始化
- 创建 admin/admin123 和 user1/user123 两个用户
- 注入 YUSHE_DAOLU 中的12条大连市真实道路数据
- 生成47条随机巡检记录和对应工单
"""

import random
from datetime import datetime, timedelta
from passlib.context import CryptContext
from database import chushihua_shujuku, ben_di_huihua
from models import User, Road, Inspection, WorkOrder
from config import YUSHE_DAOLU

# 密码哈希上下文
mima_shangxiawen = CryptContext(schemes=['bcrypt'], deprecated='auto')

# 缺陷类型池
QUESHI_LEIXING_CHI = ['坑洞', '裂缝', '龟裂', '车辙', '松散', '修补痕迹', '无']
# 严重程度池及权重
YANSONG_CHENGDU_CHI = ['轻微', '中等', '严重', '无']
YANSONG_CHENGDU_QUANZHONG = [0.35, 0.35, 0.2, 0.1]
# 紧急程度池
YINGJI_CHENGDU_CHI = ['无需处理', '低速行驶通过', '建议绕行', '立即封路']
# 缺陷位置池
QUESHI_WEIZHI_CHI = ['路面中央', '路面左侧', '路面右侧', '车道分界线处', '路肩边缘', '交叉口附近']
# 修复建议池
XIUFU_JIANYI_CHI = {
    '坑洞': ['清理坑洞松散材料后填入沥青混合料并压实', '切割坑洞边缘后用热拌沥青修补', '清理底部涂粘层油后分层填筑冷补料'],
    '裂缝': ['清理裂缝后灌入密封胶', '沿裂缝开槽后灌注沥青密封胶', '贴缝带贴缝处理'],
    '龟裂': ['铣刨面层后重新铺筑沥青混合料', '局部修补：铣刨破损区域后回填热拌料'],
    '车辙': ['铣刨车辙部位后铺筑抗车辙沥青混合料', '微表处填补车辙'],
    '松散': ['清理松散粒料后喷洒粘层油撒石屑', '表面封层处理',
              '清理松散材料后涂刷透层油'],
    '修补痕迹': ['检查修补区域边缘是否脱空，必要时重新修补', '修补边缘灌缝处理',
                  '现状观察，暂无需处理'],
    '无': ['路面状况良好，建议日常巡查即可', '保持常规养护', '暂无特殊处理建议'],
}
# 所需材料池
SUOXU_CAILIAO_CHI = {
    '坑洞': ['沥青混合料、粘层油、压实工具', '热拌沥青、乳化沥青、切割机', '冷补料、粘层油、夯平工具'],
    '裂缝': ['密封胶、开槽机、吹风机', '沥青灌缝胶、贴缝带', '聚氨酯密封胶、清理工具'],
    '龟裂': ['沥青混合料、铣刨机、压路机', '热拌料、粘层油'],
    '车辙': ['抗车辙沥青混合料、铣刨机', '微表处混合料、摊铺设备'],
    '松散': ['粘层油、石屑、撒布机', '表面封层材料、喷洒设备',
              '透层油、石屑'],
    '修补痕迹': ['沥青密封胶、灌缝机', '热拌料、修补工具', '无需材料'],
    '无': ['无需材料', '常规养护工具', '巡查记录表'],
}
# 道路状况描述池
DAOLU_ZHUANGKUANG_CHI = {
    '坑洞': ['路面存在明显坑洞，沥青面层缺失，底部裸露碎石', '坑洞边缘破碎，深度较深，影响行车安全',
              '路面局部凹陷形成坑洞，周围伴有松散碎屑'],
    '裂缝': ['路面沿车道方向出现纵向裂缝，宽度约3-5mm', '横向裂缝贯穿车道，局部有分支细裂缝',
              '网状裂缝密集，块度约10-20cm'],
    '龟裂': ['路面大面积龟裂，裂缝交织成网状，块度较小', '龟裂区域面层老化严重，伴有局部松散',
              '龟裂分布于车道轮迹带附近，面积较大'],
    '车辙': ['车道轮迹带出现明显车辙，深度约15-25mm', '车辙路段较长，雨季易积水',
              '车辙两侧伴有微小隆起'],
    '松散': ['路面表面集料脱落，出现松散现象', '沥青老化导致颗粒松散，局部已露出骨料',
              '路面磨耗层松散，雨天易掉粒'],
    '修补痕迹': ['路面存在历史修补痕迹，边缘有轻微脱空', '修补区域与原路面接缝处可见裂缝',
                  '修补材料状况尚可，边缘需关注'],
    '无': ['路面平整完好，无明显缺陷', '路面状况良好，纹理清晰', '路面外观正常，无异常损坏'],
}


def suiji_ai_jieguo():
    """生成一条随机的 AI 分析结果"""
    queshi = random.choice(QUESHI_LEIXING_CHI)
    yansong = random.choices(YANSONG_CHENGDU_CHI, weights=YANSONG_CHENGDU_QUANZHONG)[0]
    # 如果无缺陷，严重程度也为无
    if queshi == '无':
        yansong = '无'
        yingji = '无需处理'
    else:
        # 紧急程度与严重程度关联
        if yansong == '严重':
            yingji = random.choice(['建议绕行', '立即封路'])
        elif yansong == '中等':
            yingji = random.choice(['低速行驶通过', '建议绕行'])
        else:
            yingji = random.choice(['无需处理', '低速行驶通过'])

    return {
        'daolu_zhuangkuang': random.choice(DAOLU_ZHUANGKUANG_CHI[queshi]),
        'queshi_leixing': queshi,
        'yansong_chengdu': yansong,
        'queshi_weizhi': random.choice(QUESHI_WEIZHI_CHI) if queshi != '无' else '无',
        'chuli_jianyi': random.choice(XIUFU_JIANYI_CHI[queshi]),
        'suo_xu_cailiao': random.choice(SUOXU_CAILIAO_CHI[queshi]),
        'yingji_chengdu': yingji,
    }


def buzhong_shuju():
    """初始化数据库并注入种子数据"""
    chushihua_shujuku()

    db = ben_di_huihua()
    # 已有数据则跳过
    yicunzai = db.query(User).first()
    if yicunzai:
        db.close()
        return

    print('开始注入种子数据...')

    # ==================== 用户 ====================
    guanliyuan = User(
        username='admin',
        password_hash=mima_shangxiawen.hash('admin123'),
        role='admin',
        real_name='系统管理员',
        phone='13800000000',
    )
    putong_yonghu = User(
        username='user1',
        password_hash=mima_shangxiawen.hash('user123'),
        role='user',
        real_name='巡检员',
        phone='13800001111',
    )
    db.add_all([guanliyuan, putong_yonghu])
    db.flush()

    # ==================== 道路点位（大连市真实道路）====================
    daolu_jilu = []
    for yushe in YUSHE_DAOLU:
        daolu = Road(
            road_name=yushe['road_name'],
            section=yushe['section'],
            road_type=yushe['road_type'],
            latitude=yushe['latitude'],
            longitude=yushe['longitude'],
            inspector_id=putong_yonghu.id,
        )
        daolu_jilu.append(daolu)
    db.add_all(daolu_jilu)
    db.flush()

    # ==================== 47条巡检记录 ====================
    xunjian_liebiao = []
    now = datetime.now()
    # 工单触发条件
    chufa_chengdu = {'建议绕行', '立即封路'}

    for i in range(47):
        # 随机选道路
        daolu = random.choice(daolu_jilu)
        # 随机生成最近30天内的时间
        tian_shu = random.randint(0, 29)
        xiao_shi = random.randint(7, 20)
        fenzhong = random.randint(0, 59)
        shijian = now - timedelta(days=tian_shu, hours=now.hour - xiao_shi, minutes=now.minute - fenzhong)

        ai_jieguo = suiji_ai_jieguo()

        xunjian = Inspection(
            road_id=daolu.id,
            inspector_id=putong_yonghu.id,
            image_path='',  # 种子数据无图片
            ai_result=ai_jieguo,
            status='completed',
            created_at=shijian,
        )
        xunjian_liebiao.append(xunjian)

    db.add_all(xunjian_liebiao)
    db.flush()

    # ==================== 自动生成工单 ====================
    gongdan_shuliang = 0
    for xj in xunjian_liebiao:
        yingji = xj.ai_result.get('yingji_chengdu', '')
        if yingji in chufa_chengdu:
            # 随机工单状态
            zhuangtai = random.choice(['pending', 'processing', 'completed'])
            wancheng_shijian = None
            if zhuangtai == 'completed':
                wancheng_shijian = xj.created_at + timedelta(days=random.randint(1, 5))
            gongdan = WorkOrder(
                inspection_id=xj.id,
                road_id=xj.road_id,
                queshi_leixing=xj.ai_result.get('queshi_leixing', ''),
                yansong_chengdu=xj.ai_result.get('yansong_chengdu', ''),
                chuli_jianyi=xj.ai_result.get('chuli_jianyi', ''),
                status=zhuangtai,
                result_note='已完成修补处理' if zhuangtai == 'completed' else '',
                created_at=xj.created_at,
                completed_at=wancheng_shijian,
            )
            db.add(gongdan)
            gongdan_shuliang += 1

    db.commit()
    db.close()
    print(f'种子数据注入完成! 用户 2 个, 道路 {len(daolu_jilu)} 条, 巡检 {len(xunjian_liebiao)} 条, 工单 {gongdan_shuliang} 条')


if __name__ == '__main__':
    buzhong_shuju()
