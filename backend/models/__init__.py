from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default='user')
    real_name = Column(String(64), nullable=False, default='')
    phone = Column(String(20), nullable=False, default='')
    created_at = Column(DateTime, default=datetime.now)

    # 关联关系：该用户创建的巡检记录
    inspections = relationship('Inspection', back_populates='inspector', foreign_keys='Inspection.inspector_id')
    # 关联关系：该用户负责的道路
    roads = relationship('Road', back_populates='inspector_rel', foreign_keys='Road.inspector_id')


class Road(Base):
    """道路点位表"""
    __tablename__ = 'roads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    road_name = Column(String(128), nullable=False)
    section = Column(String(256), nullable=False, default='')
    road_type = Column(String(64), nullable=False, default='主干道')
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    inspector_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关联关系
    inspector_rel = relationship('User', back_populates='roads', foreign_keys=[inspector_id])
    inspections = relationship('Inspection', back_populates='road')
    workorders = relationship('WorkOrder', back_populates='road')


class Inspection(Base):
    """巡检记录表"""
    __tablename__ = 'inspections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    road_id = Column(Integer, ForeignKey('roads.id'), nullable=True)
    inspector_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    image_path = Column(String(512), nullable=False, default='')
    ai_result = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default='completed')
    created_at = Column(DateTime, default=datetime.now)

    # 关联关系
    road = relationship('Road', back_populates='inspections')
    inspector = relationship('User', back_populates='inspections', foreign_keys=[inspector_id])
    workorders = relationship('WorkOrder', back_populates='inspection')


class WorkOrder(Base):
    """工单表"""
    __tablename__ = 'workorders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(Integer, ForeignKey('inspections.id'), nullable=False)
    road_id = Column(Integer, ForeignKey('roads.id'), nullable=True)
    queshi_leixing = Column(String(64), nullable=False, default='')
    yansong_chengdu = Column(String(20), nullable=False, default='')
    chuli_jianyi = Column(Text, nullable=False, default='')
    status = Column(String(20), nullable=False, default='pending')
    result_note = Column(Text, nullable=True, default='')
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    # 关联关系
    inspection = relationship('Inspection', back_populates='workorders')
    road = relationship('Road', back_populates='workorders')
