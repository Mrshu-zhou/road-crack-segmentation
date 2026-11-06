import os

XIANGMU_GEN = os.path.dirname(os.path.abspath(__file__))
SHUJUKU_DIZHI = f"sqlite:///{os.path.join(XIANGMU_GEN, 'daolu.db')}"
SHANGCHUAN_MULU = os.path.join(XIANGMU_GEN, 'uploads')
MIYAO = os.getenv('SECRET_KEY', 'daolu-secret-key-2026')
JIAMI_SUANFA = 'HS256'
LINGPAI_GUOQI_FENZHONG = 60 * 24

DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')
DASHSCOPE_JIEKOU_DIZHI = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
DASHSCOPE_MOXING = 'qwen3.6-plus'
AI_CHAOSHI = 60

YUNXU_TUPIAN_KUOZHANMING = {'.jpg', '.jpeg', '.png', '.webp'}
ZUIDA_TUPIAN_DAXIAO = 10 * 1024 * 1024

JUESE_LIEBIAO = {
    'user': '普通用户',
    'admin': '管理员',
}

YUSHE_DAOLU = [
    {'road_name': '中山路', 'section': '中山区青泥洼桥至星海广场段', 'road_type': '主干道', 'latitude': 38.917, 'longitude': 121.614},
    {'road_name': '人民路', 'section': '中山区港湾广场至中山广场段', 'road_type': '主干道', 'latitude': 38.924, 'longitude': 121.642},
    {'road_name': '胜利路', 'section': '中山区纪念街至七星广场段', 'road_type': '主干道', 'latitude': 38.908, 'longitude': 121.628},
    {'road_name': '解放路', 'section': '中山区中山路至老虎滩段', 'road_type': '主干道', 'latitude': 38.896, 'longitude': 121.656},
    {'road_name': '黄河路', 'section': '沙河口区西安路至马栏广场段', 'road_type': '主干道', 'latitude': 38.912, 'longitude': 121.598},
    {'road_name': '西安路', 'section': '沙河口区兴工街至解放广场段', 'road_type': '主干道', 'latitude': 38.910, 'longitude': 121.605},
    {'road_name': '五四路', 'section': '沙河口区中山路至太原街段', 'road_type': '主干道', 'latitude': 38.905, 'longitude': 121.612},
    {'road_name': '中南路', 'section': '中山区桃源街至迎宾路段', 'road_type': '主干道', 'latitude': 38.882, 'longitude': 121.648},
    {'road_name': '东北大街', 'section': '金普新区经开区全段', 'road_type': '主干道', 'latitude': 39.052, 'longitude': 121.785},
    {'road_name': '旅顺南路', 'section': '高新园区黄浦路至旅顺段', 'road_type': '主干道', 'latitude': 38.876, 'longitude': 121.529},
    {'road_name': '滨海西路', 'section': '西岗区星海广场至傅家庄段', 'road_type': '次干道', 'latitude': 38.881, 'longitude': 121.622},
    {'road_name': '太原街', 'section': '沙河口区五四路至中山路段', 'road_type': '次干道', 'latitude': 38.903, 'longitude': 121.608},
]
