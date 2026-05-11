"""
用户相关的Pydantic模式
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")


class UserCreate(UserBase):
    """用户创建模式"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """用户更新模式"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="新密码")


class UserResponse(UserBase):
    """用户响应模式"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: int
    role: str = "user"
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class UserInDB(UserResponse):
    """数据库中的用户模式（包含密码哈希）"""
    hashed_password: str


class UserListResponse(BaseModel):
    """用户列表响应模式"""
    total: int
    users: list[UserResponse]
    page: int
    page_size: int
