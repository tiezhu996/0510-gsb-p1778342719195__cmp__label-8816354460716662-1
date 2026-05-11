"""
安全工具函数
包括密码加密、JWT Token生成和验证
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    加密密码
    
    Args:
        password: 明文密码
        
    Returns:
        str: 加密后的密码
    """
    # bcrypt限制密码长度不能超过72字节
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码的数据（通常包含用户ID和用户名）
        expires_delta: 过期时间增量，如果为None则使用默认值
        
    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()
    
    # 使用UTC时间，确保时区一致性
    # datetime.now(timezone.utc) 是推荐的方式，替代已弃用的 datetime.utcnow()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # JWT标准要求exp是UTC时间的Unix时间戳（整数）
    # expire已经是UTC时间，timestamp()会返回UTC时间戳
    exp_timestamp = int(expire.timestamp())
    to_encode.update({"exp": exp_timestamp})
    
    # 记录token生成信息（调试用）
    logger.debug(f"创建Token: 当前UTC时间={now.isoformat()}, 过期UTC时间={expire.isoformat()}, 过期时间戳={exp_timestamp}")
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码JWT访问令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        Optional[dict]: 解码后的数据，如果令牌无效则返回None
    """
    try:
        if not token:
            logger.warning("Token为空")
            return None
        
        # 检查 token 格式（应该是三段，用.分隔）
        parts = token.split('.')
        if len(parts) != 3:
            logger.warning(f"Token格式错误: 应该有3段，实际有{len(parts)}段")
            return None
        
        # 解码token，python-jose会自动验证exp和签名
        # 直接使用标准解码，让python-jose处理所有验证
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # 记录成功解码的信息
        if "exp" in payload:
            exp_timestamp = payload["exp"]
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            now_timestamp = int(now.timestamp())
            remaining_seconds = exp_timestamp - now_timestamp
            logger.info(f"Token验证成功: 用户ID={payload.get('sub')}, "
                       f"当前UTC时间={now.isoformat()}, "
                       f"过期UTC时间={exp_datetime.isoformat()}, "
                       f"剩余时间={remaining_seconds}秒 ({remaining_seconds//60}分钟)")
        
        logger.debug(f"Token解码成功: 用户ID={payload.get('sub')}")
        return payload
    except jwt.ExpiredSignatureError as e:
        # 这个异常是python-jose在验证exp时抛出的
        logger.warning(f"Token已过期 (ExpiredSignatureError): {e}")
        # 尝试获取过期时间用于详细日志
        try:
            unverified = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM], 
                options={"verify_signature": True, "verify_exp": False}
            )
            if "exp" in unverified:
                exp_timestamp = unverified["exp"]
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                now = datetime.now(timezone.utc)
                now_timestamp = int(now.timestamp())
                expired_seconds = now_timestamp - exp_timestamp
                logger.warning(f"Token过期详情: 用户ID={unverified.get('sub')}, "
                             f"当前UTC时间={now.isoformat()} (时间戳={now_timestamp}), "
                             f"过期UTC时间={exp_datetime.isoformat()} (时间戳={exp_timestamp}), "
                             f"已过期{expired_seconds}秒 ({expired_seconds//60}分钟)")
                logger.warning(f"可能原因: 1) Token真的已过期 2) 系统时间不同步 3) Token生成时使用了错误的时区")
        except Exception as decode_error:
            logger.warning(f"无法获取Token过期详情: {type(decode_error).__name__}: {decode_error}")
        return None
    except jwt.InvalidSignatureError as e:
        logger.warning(f"Token签名验证失败: 可能SECRET_KEY不匹配 - {e}")
        logger.warning(f"当前SECRET_KEY长度: {len(settings.SECRET_KEY) if settings.SECRET_KEY else 0}")
        return None
    except jwt.JWTClaimsError as e:
        logger.warning(f"Token声明验证失败: {e}")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token无效: {type(e).__name__}: {e}")
        return None
    except JWTError as e:
        logger.warning(f"JWT错误: {type(e).__name__}: {e}")
        return None
    except Exception as e:
        logger.error(f"解码Token时发生未知错误: {type(e).__name__}: {e}", exc_info=True)
        return None

