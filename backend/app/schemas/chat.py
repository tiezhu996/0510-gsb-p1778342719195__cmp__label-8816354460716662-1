"""
聊天相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== 聊天室相关 ==========

class ChatRoomCreate(BaseModel):
    """创建聊天室的请求模式"""
    name: str = Field(..., min_length=1, max_length=100, description="聊天室名称")
    description: Optional[str] = Field(None, description="聊天室描述")
    is_public: bool = Field(True, description="是否公开")


class ChatRoomResponse(BaseModel):
    """聊天室响应模式"""
    id: int
    name: str
    description: Optional[str] = None
    creator_id: int
    is_public: bool
    created_at: datetime
    updated_at: datetime
    creator_username: Optional[str] = None
    member_count: Optional[int] = None  # 成员数量
    
    class Config:
        from_attributes = True


class ChatRoomListResponse(BaseModel):
    """聊天室列表响应模式"""
    total: int
    rooms: list[ChatRoomResponse]
    page: int
    page_size: int


# ========== 群聊消息相关 ==========

class ChatMessageCreate(BaseModel):
    """创建群聊消息的请求模式"""
    content: str = Field(..., min_length=1, description="消息内容")
    message_type: str = Field("text", description="消息类型（text, image, file等）")


class ChatMessageResponse(BaseModel):
    """群聊消息响应模式"""
    id: int
    room_id: int
    sender_id: int
    content: str
    message_type: str
    created_at: datetime
    sender_username: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChatMessageListResponse(BaseModel):
    """群聊消息列表响应模式"""
    total: int
    messages: list[ChatMessageResponse]
    page: int
    page_size: int


# ========== 私聊消息相关 ==========

class PrivateMessageCreate(BaseModel):
    """创建私聊消息的请求模式"""
    content: str = Field(..., min_length=1, description="消息内容")
    message_type: str = Field("text", description="消息类型（text, image, file等）")


class PrivateMessageResponse(BaseModel):
    """私聊消息响应模式"""
    id: int
    sender_id: int
    receiver_id: int
    content: str
    message_type: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    sender_username: Optional[str] = None
    receiver_username: Optional[str] = None
    
    class Config:
        from_attributes = True


class PrivateMessageListResponse(BaseModel):
    """私聊消息列表响应模式"""
    total: int
    messages: list[PrivateMessageResponse]
    page: int
    page_size: int


# ========== 私聊会话相关 ==========

class ConversationResponse(BaseModel):
    """私聊会话响应模式"""
    user_id: int
    username: str
    last_message: Optional[PrivateMessageResponse] = None
    unread_count: int = 0
    last_message_at: Optional[datetime] = None


class ConversationListResponse(BaseModel):
    """私聊会话列表响应模式"""
    conversations: list[ConversationResponse]


# ========== WebSocket消息格式 ==========

class WebSocketMessage(BaseModel):
    """WebSocket消息基础模式"""
    type: str = Field(..., description="消息类型")
    

class ChatMessageWS(BaseModel):
    """WebSocket群聊消息"""
    type: str = "chat_message"
    room_id: int
    content: str
    message_type: str = "text"


class PrivateMessageWS(BaseModel):
    """WebSocket私聊消息"""
    type: str = "private_message"
    receiver_id: int
    content: str
    message_type: str = "text"


class JoinRoomWS(BaseModel):
    """WebSocket加入房间消息"""
    type: str = "join_room"
    room_id: int


class LeaveRoomWS(BaseModel):
    """WebSocket离开房间消息"""
    type: str = "leave_room"
    room_id: int

