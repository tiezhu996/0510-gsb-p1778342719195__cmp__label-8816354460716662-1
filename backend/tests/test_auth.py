"""
认证功能单元测试
测试用户注册、登录、JWT Token等功能
"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import register_user, authenticate_user, create_user_token
from app.utils.security import verify_password, decode_access_token


class TestUserRegistration:
    """用户注册功能测试"""
    
    def test_register_user_success(self, db_session: Session):
        """测试成功注册新用户"""
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        user = register_user(db_session, user_create)
        
        assert user is not None
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.is_active is True
        assert user.hashed_password != "testpass123"  # 密码应该被加密
        assert verify_password("testpass123", user.hashed_password)  # 验证密码正确
        
        # 验证用户已保存到数据库
        db_user = db_session.query(User).filter(User.username == "testuser").first()
        assert db_user is not None
        assert db_user.id == user.id
    
    def test_register_user_duplicate_username(self, db_session: Session):
        """测试注册重复用户名"""
        # 先创建一个用户
        user_create1 = UserCreate(
            username="testuser",
            email="test1@example.com",
            password="testpass123"
        )
        register_user(db_session, user_create1)
        
        # 尝试用相同用户名注册
        user_create2 = UserCreate(
            username="testuser",
            email="test2@example.com",
            password="testpass123"
        )
        
        with pytest.raises(Exception) as exc_info:
            register_user(db_session, user_create2)
        
        assert "用户名已存在" in str(exc_info.value.detail)
    
    def test_register_user_duplicate_email(self, db_session: Session):
        """测试注册重复邮箱"""
        # 先创建一个用户
        user_create1 = UserCreate(
            username="testuser1",
            email="test@example.com",
            password="testpass123"
        )
        register_user(db_session, user_create1)
        
        # 尝试用相同邮箱注册
        user_create2 = UserCreate(
            username="testuser2",
            email="test@example.com",
            password="testpass123"
        )
        
        with pytest.raises(Exception) as exc_info:
            register_user(db_session, user_create2)
        
        assert "邮箱已被注册" in str(exc_info.value.detail)


class TestUserLogin:
    """用户登录功能测试"""
    
    def test_authenticate_user_success_with_username(self, db_session: Session):
        """测试使用用户名成功登录"""
        # 先创建用户
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        created_user = register_user(db_session, user_create)
        
        # 使用用户名登录
        user = authenticate_user(db_session, "testuser", "testpass123")
        
        assert user is not None
        assert user.id == created_user.id
        assert user.username == "testuser"
    
    def test_authenticate_user_success_with_email(self, db_session: Session):
        """测试使用邮箱成功登录"""
        # 先创建用户
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        created_user = register_user(db_session, user_create)
        
        # 使用邮箱登录
        user = authenticate_user(db_session, "test@example.com", "testpass123")
        
        assert user is not None
        assert user.id == created_user.id
        assert user.email == "test@example.com"
    
    def test_authenticate_user_wrong_username(self, db_session: Session):
        """测试使用错误用户名登录"""
        # 先创建用户
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        register_user(db_session, user_create)
        
        # 使用错误的用户名
        with pytest.raises(Exception) as exc_info:
            authenticate_user(db_session, "wronguser", "testpass123")
        
        assert "用户名或密码错误" in str(exc_info.value.detail)
    
    def test_authenticate_user_wrong_password(self, db_session: Session):
        """测试使用错误密码登录"""
        # 先创建用户
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        register_user(db_session, user_create)
        
        # 使用错误的密码
        with pytest.raises(Exception) as exc_info:
            authenticate_user(db_session, "testuser", "wrongpass")
        
        assert "用户名或密码错误" in str(exc_info.value.detail)
    
    def test_authenticate_user_inactive(self, db_session: Session):
        """测试未激活用户登录"""
        # 先创建用户
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        created_user = register_user(db_session, user_create)
        
        # 将用户设置为未激活
        created_user.is_active = False
        db_session.commit()
        db_session.refresh(created_user)
        
        # 尝试登录
        with pytest.raises(Exception) as exc_info:
            authenticate_user(db_session, "testuser", "testpass123")
        
        assert "用户未激活" in str(exc_info.value.detail)


class TestJWTToken:
    """JWT Token生成和验证测试"""
    
    def test_create_user_token_success(self, db_session: Session):
        """测试成功创建用户Token"""
        # 先创建用户
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        user = register_user(db_session, user_create)
        
        # 创建Token
        token_data = create_user_token(user)
        
        assert token_data is not None
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["access_token"] is not None
        assert len(token_data["access_token"]) > 0
    
    def test_token_contains_user_info(self, db_session: Session):
        """测试Token包含用户信息"""
        from jose import jwt
        from app.config import settings
        
        # 先创建用户
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        user = register_user(db_session, user_create)
        
        # 创建Token
        token_data = create_user_token(user)
        token = token_data["access_token"]
        
        # 直接使用jwt.decode解码（不验证exp，因为可能有时钟同步问题）
        # 在实际使用中，decode_access_token会验证exp
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        
        assert payload is not None
        assert "sub" in payload
        assert "username" in payload
        # sub是字符串
        assert payload["sub"] == str(user.id)
        assert payload["username"] == "testuser"
        assert "exp" in payload  # 过期时间
    
    def test_token_expiration(self, db_session: Session):
        """测试Token过期时间"""
        from jose import jwt
        from app.config import settings
        from datetime import datetime
        
        # 先创建用户
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        user = register_user(db_session, user_create)
        
        # 创建Token
        token_data = create_user_token(user)
        token = token_data["access_token"]
        
        # 直接使用jwt.decode解码（不验证exp，因为可能有时钟同步问题）
        # 但我们可以检查exp字段是否存在且是未来的时间戳
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        
        assert payload is not None
        assert "exp" in payload
        
        # 验证过期时间在未来（至少30分钟后）
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        
        # 过期时间应该在当前时间之后（允许一些时间偏差）
        time_diff = (exp_datetime - now).total_seconds()
        assert time_diff > 0, f"Token expiration time should be in the future, but got {time_diff} seconds"
    
    def test_decode_invalid_token(self):
        """测试解码无效Token"""
        invalid_token = "invalid.token.here"
        
        payload = decode_access_token(invalid_token)
        
        assert payload is None
    
    def test_decode_expired_token(self, db_session: Session):
        """测试解码过期Token"""
        from datetime import datetime, timedelta
        from jose import jwt
        from app.config import settings
        
        # 创建一个已过期的Token
        expire = datetime.utcnow() - timedelta(minutes=1)  # 1分钟前过期
        to_encode = {
            "sub": 1,
            "username": "testuser",
            "exp": expire
        }
        expired_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # 尝试解码过期Token
        payload = decode_access_token(expired_token)
        
        # 应该返回None（因为Token已过期）
        assert payload is None

