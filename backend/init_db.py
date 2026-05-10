"""
数据库初始化脚本
创建数据库文件并初始化所有表
"""
import os
from app.database import engine, Base
from app.config import settings

def init_database():
    """初始化数据库"""
    # 确保数据库目录存在
    db_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", ""))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"创建数据库目录: {db_dir}")
    
    # 导入所有模型，确保它们被注册到Base.metadata
    # 注意：在模型文件创建后，需要在这里导入
    from app.models import User, ChatRoom, ChatMessage, PrivateMessage  # noqa: F401
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")
    print(f"数据库位置: {settings.DATABASE_URL}")

if __name__ == "__main__":
    init_database()

