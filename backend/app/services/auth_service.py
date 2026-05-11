"""
认证服务
处理用户注册、登录等认证相关业务逻辑
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.utils.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.config import settings


def register_user(db: Session, user_create: UserCreate) -> User:
    """
    注册新用户
    
    Args:
        db: 数据库会话
        user_create: 用户创建数据
        
    Returns:
        User: 创建的用户对象
        
    Raises:
        HTTPException: 如果用户名或邮箱已存在
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_create.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_create.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password,
        role="user",
        is_active=True
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户创建失败，可能用户名或邮箱已存在"
        )


def authenticate_user(db: Session, username: str, password: str) -> User:
    """
    验证用户登录
    
    Args:
        db: 数据库会话
        username: 用户名
        password: 密码
        
    Returns:
        User: 用户对象
        
    Raises:
        HTTPException: 如果用户名或密码错误，或用户未激活
    """
    # 查找用户（支持用户名或邮箱登录）
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    
    return user


def create_user_token(user: User) -> dict:
    """
    为用户创建访问令牌
    
    Args:
        user: 用户对象
        
    Returns:
        dict: 包含access_token和token_type的字典
    """
    # 创建令牌数据
    # JWT标准中sub应该是字符串，但python-jose也支持整数
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

