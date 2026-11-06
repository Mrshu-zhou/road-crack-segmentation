from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import SHUJUKU_DIZHI

yinqing = create_engine(SHUJUKU_DIZHI, connect_args={'check_same_thread': False})
ben_di_huihua = sessionmaker(autocommit=False, autoflush=False, bind=yinqing)


class Base(DeclarativeBase):
    pass


def huoqu_shujuku():
    db = ben_di_huihua()
    try:
        yield db
    finally:
        db.close()


def chushihua_shujuku():
    from models import User, Road, Inspection, WorkOrder
    Base.metadata.create_all(bind=yinqing)
