"""
FastAPI依赖注入函数
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token

# OAuth2密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 可选的OAuth2密码流（不强制要求token）
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)



async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    
    Args:
        token: JWT令牌
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 如果令牌无效或用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 解码令牌
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # 从payload中获取用户ID
    # sub可能是字符串或整数，需要转换
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    try:
        user_id: int = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception
    
    # 从数据库获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前激活的用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 激活的用户对象
        
    Raises:
        HTTPException: 如果用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> User | None:
    """
    可选的用户认证依赖：如果用户已登录则返回用户对象，否则返回None
    
    用于支持匿名和登录用户都能访问的端点
    
    Args:
        request: FastAPI Request 对象
        db: 数据库会话
        
    Returns:
        User | None: 用户对象（如果已登录），否则返回None
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 手动从 Authorization header 中提取 token
    authorization: str = request.headers.get("Authorization")
    
    if not authorization:
        logger.info("get_current_user_optional: 没有 Authorization header")
        return None
    
    # 检查格式是否为 "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(f"get_current_user_optional: Authorization header 格式不正确: {authorization[:20]}...")
        return None
    
    token = parts[1]
    logger.info(f"get_current_user_optional: 提取到 token: {token[:20]}...")
    
    try:
        # 解码令牌
        payload = decode_access_token(token)
        if payload is None:
            logger.warning("get_current_user_optional: token解码失败")
            return None
        
        # 从payload中获取用户ID
        user_id_str = payload.get("sub")
        if user_id_str is None:
            logger.warning("get_current_user_optional: payload中没有sub字段")
            return None
        
        try:
            user_id: int = int(user_id_str)
        except (ValueError, TypeError):
            logger.warning(f"get_current_user_optional: 无法将sub转换为整数: {user_id_str}")
            return None
        
        # 从数据库获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            logger.warning(f"get_current_user_optional: 用户不存在或未激活: user_id={user_id}")
            return None
        
        logger.info(f"get_current_user_optional: 成功获取用户: user_id={user_id}, username={user.username}")
        return user
    except Exception as e:
        # 任何异常都返回None（匿名用户）
        logger.error(f"get_current_user_optional: 发生异常: {str(e)}")
        return None

