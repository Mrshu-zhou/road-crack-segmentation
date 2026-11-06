from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt

from database import huoqu_shujuku
from models import User
from config import MIYAO, JIAMI_SUANFA, LINGPAI_GUOQI_FENZHONG

router = APIRouter(prefix='/api/auth', tags=['auth'])
# 密码哈希上下文，使用 bcrypt
mima_shangxiawen = CryptContext(schemes=['bcrypt'], deprecated='auto')


class DengluQingqiu(BaseModel):
    """登录请求体"""
    username: str
    password: str


class LingpaiXiangying(BaseModel):
    """登录响应体"""
    access_token: str
    token_type: str = 'bearer'
    user: dict


def jianli_fangwen_lingpai(shuju: dict) -> str:
    """生成 JWT 访问令牌"""
    bianma_shuju = shuju.copy()
    guoqi_shijian = datetime.utcnow() + timedelta(minutes=LINGPAI_GUOQI_FENZHONG)
    bianma_shuju.update({'exp': guoqi_shijian})
    return jwt.encode(bianma_shuju, MIYAO, algorithm=JIAMI_SUANFA)


def huoqu_dangqian_yonghu(authorization: str = Header(None), db: Session = Depends(huoqu_shujuku)) -> User:
    """解析 Authorization header 中的 JWT，返回当前登录用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail='未登录')
    lingpai = authorization.replace('Bearer ', '').strip()
    if not lingpai:
        raise HTTPException(status_code=401, detail='Token不能为空')
    try:
        fuhe = jwt.decode(lingpai, MIYAO, algorithms=[JIAMI_SUANFA])
        yonghu_id = fuhe.get('user_id')
        if yonghu_id is None:
            raise HTTPException(status_code=401, detail='Token无效')
    except Exception:
        raise HTTPException(status_code=401, detail='Token无效或已过期')
    yonghu = db.query(User).filter(User.id == yonghu_id).first()
    if yonghu is None:
        raise HTTPException(status_code=401, detail='用户不存在')
    return yonghu


@router.post('/login', response_model=LingpaiXiangying)
def denglu(qingqiu: DengluQingqiu, db: Session = Depends(huoqu_shujuku)):
    """用户名+密码登录，返回 JWT token 和用户信息"""
    yonghu = db.query(User).filter(User.username == qingqiu.username).first()
    if not yonghu or not mima_shangxiawen.verify(qingqiu.password, yonghu.password_hash):
        raise HTTPException(status_code=401, detail='用户名或密码错误')
    lingpai = jianli_fangwen_lingpai({'user_id': yonghu.id, 'role': yonghu.role})
    return LingpaiXiangying(
        access_token=lingpai,
        user={
            'id': yonghu.id,
            'username': yonghu.username,
            'role': yonghu.role,
            'real_name': yonghu.real_name,
            'phone': yonghu.phone,
        },
    )


@router.get('/me')
def wo_de_xinxi(yonghu: User = Depends(huoqu_dangqian_yonghu)):
    """获取当前登录用户信息"""
    return {
        'id': yonghu.id,
        'username': yonghu.username,
        'role': yonghu.role,
        'real_name': yonghu.real_name,
        'phone': yonghu.phone,
    }
