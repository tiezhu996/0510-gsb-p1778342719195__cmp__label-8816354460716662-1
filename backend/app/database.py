"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 创建数据库引擎
# SQLite需要使用check_same_thread=False
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.ENVIRONMENT == "development"
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """
    获取数据库会话的依赖注入函数
    """
    db = SessionLocal()
    try:
        yield db
        # 请求成功完成后，自动提交事务
        db.commit()
    except Exception:
        # 发生异常时回滚
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    初始化数据库，创建所有表
    """
    Base.metadata.create_all(bind=engine)

