"""
pytest配置文件
提供测试用的数据库会话和测试客户端
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app.config import settings

# 导入所有模型，确保它们被注册到Base.metadata
from app.models import User, ChatRoom, ChatMessage, PrivateMessage  # noqa: F401


# 创建测试数据库（使用内存数据库）
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """
    为每个测试函数创建独立的数据库会话
    测试结束后自动回滚
    """
    # 创建所有表
    Base.metadata.create_all(bind=test_engine)
    
    # 创建会话
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # 删除所有表
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    创建测试客户端，使用测试数据库会话
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # 创建TestClient - 直接使用位置参数
    test_client = TestClient(app)
    yield test_client
    
    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers(client, db_session):
    """
    创建测试用户并返回认证headers
    返回一个函数，可以获取认证headers
    """
    def _get_auth_headers(username="testuser", password="password123"):
        from app.models.user import User
        from app.utils.security import get_password_hash, create_access_token
        from datetime import timedelta
        from app.config import settings
        
        # 检查用户是否已存在
        user = db_session.query(User).filter(User.username == username).first()
        if not user:
            # 创建用户
            user = User(
                username=username,
                email=f"{username}@example.com",
                hashed_password=get_password_hash(password),
                role="user",
                is_active=True
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
        
        # 直接生成token，使用更长的过期时间（24小时）
        token_data = {
            "sub": str(user.id),
            "username": user.username
        }
        token = create_access_token(
            data=token_data,
            expires_delta=timedelta(hours=24)
        )
        
        return {"Authorization": f"Bearer {token}"}
    
    return _get_auth_headers
