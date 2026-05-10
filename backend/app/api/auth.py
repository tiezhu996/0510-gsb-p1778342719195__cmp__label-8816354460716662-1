"""
认证相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import User
from app.services.auth_service import register_user, authenticate_user, create_user_token
from app.utils.dependencies import get_current_active_user
import logging

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/test-register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_test():
    """
    测试注册接口 - 返回模拟数据，不涉及数据库操作
    用于排除前后端连接和序列化问题
    注意：此路由必须在 /register 之前定义，因为FastAPI按顺序匹配路由
    """
    from datetime import datetime
    # 创建模拟的用户响应数据
    mock_user_data = {
        "id": 999,
        "username": "testuser",
        "email": "test@example.com",
        "role": "user",
        "avatar_url": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "is_active": True
    }
    try:
        # 直接创建UserResponse对象，不涉及数据库
        response_data = UserResponse(**mock_user_data)
        return response_data
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"测试接口序列化失败: {str(e)}")
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试接口失败: {str(e)}"
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    - **username**: 用户名（3-50个字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少6个字符）
    """
    logger = logging.getLogger(__name__)
    logger.info("注册接口被调用")
    logger.info(f"接收到的数据: username={user_create.username}, email={user_create.email}")
    
    try:
        # 调用服务层注册用户（数据库操作）
        logger.info("开始调用register_user服务...")
        user = register_user(db, user_create)
        logger.info(f"用户创建成功: id={user.id}, username={user.username}, email={user.email}")
        
        # 将数据库对象转换为响应数据（datetime转换为ISO格式字符串）
        try:
            # 先转换为字典，手动处理datetime
            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "is_active": user.is_active
            }
            
            # 验证数据格式
            response_obj = UserResponse(**user_dict)
            logger.info(f"UserResponse对象创建成功: {response_obj.username}")
            
            # 直接返回字典，让FastAPI自动序列化（避免response_model序列化问题）
            logger.info(f"准备返回数据: id={user_dict['id']}, username={user_dict['username']}")
            return user_dict
            
        except Exception as serialization_error:
            logger.error(f"序列化用户数据失败: {str(serialization_error)}")
            logger.error(f"用户对象: id={user.id}, username={user.username}, email={user.email}")
            logger.error(f"created_at类型: {type(user.created_at)}, 值: {user.created_at}")
            logger.error(f"updated_at类型: {type(user.updated_at)}, 值: {user.updated_at}")
            import traceback
            logger.error(f"序列化错误堆栈: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"序列化用户数据失败: {str(serialization_error)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"注册失败: {str(e)}")
        logger.error(f"异常类型: {type(e).__name__}")
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login")
async def login(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    
    返回访问令牌和用户信息
    """
    user = authenticate_user(db, user_login.username, user_login.password)
    token_data = create_user_token(user)
    
    return {
        **token_data,
        "user": UserResponse.model_validate(user)
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    用户登出
    
    注意：由于使用JWT，客户端需要删除存储的token
    这里只是返回成功消息
    """
    return {"message": "成功登出"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前登录用户信息
    
    需要提供有效的JWT令牌
    """
    return UserResponse.model_validate(current_user)

