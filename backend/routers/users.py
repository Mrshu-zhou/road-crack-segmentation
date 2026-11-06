from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext

from database import huoqu_shujuku
from models import User
from routers.auth import huoqu_dangqian_yonghu
from config import JUESE_LIEBIAO

router = APIRouter(prefix='/api/users', tags=['users'])
mima_shangxiawen = CryptContext(schemes=['bcrypt'], deprecated='auto')


class YonghuChuangjian(BaseModel):
    """新建用户请求体"""
    username: str
    password: str
    role: str = 'user'
    real_name: str = ''
    phone: str = ''


@router.get('')
def yonghu_liebiao(yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """获取用户列表（仅管理员）"""
    if yonghu.role != 'admin':
        raise HTTPException(status_code=403, detail='仅管理员可查看用户列表')
    yonghu_jilu = db.query(User).all()
    return {
        'users': [
            {
                'id': u.id,
                'username': u.username,
                'role': u.role,
                'real_name': u.real_name,
                'phone': u.phone,
                'created_at': u.created_at.isoformat() if u.created_at else '',
            }
            for u in yonghu_jilu
        ],
        'roles': JUESE_LIEBIAO,
    }


@router.post('')
def chuangjian_yonghu(shuju: YonghuChuangjian, yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """新建用户（仅管理员）"""
    if yonghu.role != 'admin':
        raise HTTPException(status_code=403, detail='仅管理员可创建用户')
    if shuju.role not in JUESE_LIEBIAO:
        raise HTTPException(status_code=400, detail='无效角色，可选: user/admin')
    yicunzai = db.query(User).filter(User.username == shuju.username).first()
    if yicunzai:
        raise HTTPException(status_code=400, detail='用户名已存在')
    xinyonghu = User(
        username=shuju.username,
        password_hash=mima_shangxiawen.hash(shuju.password),
        role=shuju.role,
        real_name=shuju.real_name,
        phone=shuju.phone,
    )
    db.add(xinyonghu)
    db.commit()
    db.refresh(xinyonghu)
    return {'id': xinyonghu.id, 'message': '用户创建成功'}


class YonghuBianji(BaseModel):
    """编辑用户请求体"""
    role: str = None
    real_name: str = None
    phone: str = None
    password: str = None


@router.put('/{yonghu_id}')
def bianji_yonghu(yonghu_id: int, shuju: YonghuBianji, yonghu: User = Depends(huoqu_dangqian_yonghu), db: Session = Depends(huoqu_shujuku)):
    """编辑用户信息（仅管理员）"""
    if yonghu.role != 'admin':
        raise HTTPException(status_code=403, detail='仅管理员可编辑用户')
    mubiao = db.query(User).filter(User.id == yonghu_id).first()
    if not mubiao:
        raise HTTPException(status_code=404, detail='用户不存在')
    if shuju.role is not None:
        if shuju.role not in JUESE_LIEBIAO:
            raise HTTPException(status_code=400, detail='无效角色')
        mubiao.role = shuju.role
    if shuju.real_name is not None:
        mubiao.real_name = shuju.real_name
    if shuju.phone is not None:
        mubiao.phone = shuju.phone
    if shuju.password:
        mubiao.password_hash = mima_shangxiawen.hash(shuju.password)
    db.commit()
    return {'message': '用户更新成功'}
