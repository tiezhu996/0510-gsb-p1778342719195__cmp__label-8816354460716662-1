"""
聊天相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
import pydantic
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.chat import room_members
from app.schemas.chat import (
    ChatRoomCreate,
    ChatRoomResponse,
    ChatRoomListResponse,
    ChatMessageResponse,
    ChatMessageListResponse,
    PrivateMessageResponse,
    PrivateMessageListResponse,
    ConversationResponse,
    ConversationListResponse
)
from app.services.chat_service import (
    create_chat_room,
    delete_chat_room,
    invite_user_to_room,
    get_chat_room,
    get_chat_rooms,
    join_chat_room,
    leave_chat_room,
    get_room_member_count,
    get_chat_messages,
    get_private_messages,
    get_user_conversations,
    mark_message_read,
    get_unread_count
)
from app.websocket.connection_manager import manager
from app.utils.dependencies import get_current_active_user, get_current_user_optional


router = APIRouter(prefix="/api/chat", tags=["Chat"])


# ========== 聊天室相关 ==========

@router.get("/rooms", response_model=ChatRoomListResponse)
async def get_chat_rooms_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID（筛选用户加入的聊天室）"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取聊天室列表
    
    支持匿名和登录用户访问：
    - 未登录用户：只能看到公开聊天室
    - 登录用户：可以看到公开聊天室 + 自己加入的非公开聊天室
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（1-100）
    - **user_id**: 用户ID（可选，筛选用户加入的聊天室）
    - **is_public**: 是否公开（可选，筛选公开/私有聊天室）
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 获取当前用户ID（如果已登录）
    current_user_id = current_user.id if current_user else None
    
    logger.info(f"get_chat_rooms_list: current_user={current_user}, current_user_id={current_user_id}, is_public={is_public}, user_id={user_id}")
    
    rooms, total = get_chat_rooms(
        db, 
        page=page, 
        page_size=page_size, 
        user_id=user_id, 
        is_public=is_public,
        current_user_id=current_user_id
    )
    
    # 构建响应数据
    rooms_data = []
    for room in rooms:
        member_count = get_room_member_count(db, room.id)
        room_dict = {
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "creator_id": room.creator_id,
            "is_public": room.is_public,
            "created_at": room.created_at,
            "updated_at": room.updated_at,
            "creator_username": room.creator.username if room.creator else None,
            "member_count": member_count
        }
        rooms_data.append(ChatRoomResponse(**room_dict))
    
    return ChatRoomListResponse(
        total=total,
        rooms=rooms_data,
        page=page,
        page_size=page_size
    )



@router.post("/rooms", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_room_endpoint(
    room_create: ChatRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建聊天室
    
    需要登录
    """
    room = create_chat_room(db, room_create, current_user.id)
    member_count = get_room_member_count(db, room.id)
    
    return ChatRoomResponse(
        id=room.id,
        name=room.name,
        description=room.description,
        creator_id=room.creator_id,
        is_public=room.is_public,
        created_at=room.created_at,
        updated_at=room.updated_at,
        creator_username=current_user.username,
        member_count=member_count
    )


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_room_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除聊天室
    
    需要登录，且必须是创建者
    """
    # 1. 获取房间信息（用于通知）
    room = get_chat_room(db, room_id)
    if not room:
        # 如果房间不存在，直接返回（或者抛出404，但delete_chat_room会处理）
        pass
        
    # 2. 获取成员列表（在删除前）
    # 直接查询中间表，避免ORM延迟加载的问题
    members_to_notify = []
    if room:
        stmt = select(room_members.c.user_id).where(room_members.c.room_id == room_id)
        result = db.execute(stmt).fetchall()
        # result是(user_id,)的列表
        members_to_notify = [row[0] for row in result]
        
        if room.creator_id not in members_to_notify:
            members_to_notify.append(room.creator_id)
    
    # 3. 删除房间
    delete_chat_room(db, room_id, current_user.id)
    
    # 4. 发送实时通知给所有成员
    for member_id in members_to_notify:
        await manager.send_personal_message(
            {
                "type": "room_deleted",
                "room_id": room_id
            },
            member_id
        )
    return


class InviteRequest(pydantic.BaseModel):
    username: str


@router.post("/rooms/{room_id}/invite", status_code=status.HTTP_200_OK)
async def invite_user_endpoint(
    room_id: int,
    start_request: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    邀请用户加入聊天室
    
    需要登录，且必须是创建者
    """
    invited_user = invite_user_to_room(db, room_id, current_user.id, start_request.username)
    
    # 获取房间信息用于通知
    room = get_chat_room(db, room_id)
    
    # 发送实时通知给被邀请者
    await manager.send_personal_message(
        {
            "type": "room_invited",
            "room_id": room_id,
            "room_name": room.name,
            "inviter_username": current_user.username
        },
        invited_user.id
    )
    
    return {"message": "邀请成功"}


@router.get("/rooms/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room_detail(
    room_id: int,
    db: Session = Depends(get_db)
):
    """
    获取聊天室详情
    """
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )
    
    member_count = get_room_member_count(db, room.id)
    
    return ChatRoomResponse(
        id=room.id,
        name=room.name,
        description=room.description,
        creator_id=room.creator_id,
        is_public=room.is_public,
        created_at=room.created_at,
        updated_at=room.updated_at,
        creator_username=room.creator.username if room.creator else None,
        member_count=member_count
    )


@router.post("/rooms/{room_id}/join", status_code=status.HTTP_200_OK)
async def join_chat_room_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    加入聊天室
    
    需要登录
    """
    join_chat_room(db, room_id, current_user.id)
    return {"message": "成功加入聊天室"}


@router.post("/rooms/{room_id}/leave", status_code=status.HTTP_200_OK)
async def leave_chat_room_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    离开聊天室
    
    需要登录
    """
    leave_chat_room(db, room_id, current_user.id)
    return {"message": "成功离开聊天室"}


@router.get("/rooms/{room_id}/messages", response_model=ChatMessageListResponse)
async def get_chat_room_messages(
    room_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取聊天室消息历史
    
    需要登录，且用户必须在聊天室中
    """
    # 检查聊天室是否存在
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )
    
    messages, total = get_chat_messages(db, room_id, page=page, page_size=page_size)
    
    # 构建响应数据
    messages_data = []
    for message in messages:
        message_dict = {
            "id": message.id,
            "room_id": message.room_id,
            "sender_id": message.sender_id,
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at,
            "sender_username": message.sender.username if message.sender else None
        }
        messages_data.append(ChatMessageResponse(**message_dict))
    
    return ChatMessageListResponse(
        total=total,
        messages=messages_data,
        page=page,
        page_size=page_size
    )


# ========== 私聊相关 ==========

@router.get("/private/conversations", response_model=ConversationListResponse)
async def get_private_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取用户的私聊会话列表
    
    需要登录
    """
    conversations_data = get_user_conversations(db, current_user.id)
    
    # 构建响应数据
    conversations = []
    for conv in conversations_data:
        conversation = ConversationResponse(
            user_id=conv['user_id'],
            username=conv['username'],
            last_message=PrivateMessageResponse(
                id=conv['last_message'].id,
                sender_id=conv['last_message'].sender_id,
                receiver_id=conv['last_message'].receiver_id,
                content=conv['last_message'].content,
                message_type=conv['last_message'].message_type,
                is_read=conv['last_message'].is_read,
                read_at=conv['last_message'].read_at,
                created_at=conv['last_message'].created_at,
                sender_username=conv['last_message'].sender.username if conv['last_message'].sender else None,
                receiver_username=conv['last_message'].receiver.username if conv['last_message'].receiver else None
            ) if conv['last_message'] else None,
            unread_count=conv['unread_count'],
            last_message_at=conv['last_message_at']
        )
        conversations.append(conversation)
    
    return ConversationListResponse(conversations=conversations)


@router.get("/private/{user_id}/messages", response_model=PrivateMessageListResponse)
async def get_private_messages_endpoint(
    user_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取与指定用户的私聊消息历史
    
    需要登录
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能获取与自己的私聊消息"
        )
    
    messages, total = get_private_messages(db, current_user.id, user_id, page=page, page_size=page_size)
    
    # 构建响应数据
    messages_data = []
    for message in messages:
        message_dict = {
            "id": message.id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "message_type": message.message_type,
            "is_read": message.is_read,
            "read_at": message.read_at,
            "created_at": message.created_at,
            "sender_username": message.sender.username if message.sender else None,
            "receiver_username": message.receiver.username if message.receiver else None
        }
        messages_data.append(PrivateMessageResponse(**message_dict))
    
    return PrivateMessageListResponse(
        total=total,
        messages=messages_data,
        page=page,
        page_size=page_size
    )


@router.put("/private/messages/{message_id}/read", status_code=status.HTTP_200_OK)
async def mark_message_read_endpoint(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    标记私聊消息为已读
    
    需要登录
    """
    mark_message_read(db, message_id, current_user.id)
    return {"message": "消息已标记为已读"}


@router.get("/private/unread-count")
async def get_unread_count_endpoint(
    sender_id: Optional[int] = Query(None, description="发送者ID（可选，用于获取特定发送者的未读消息数）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取用户的未读消息数量
    
    需要登录
    """
    count = get_unread_count(db, current_user.id, sender_id)
    return {"unread_count": count}


# ========== 在线用户相关 ==========

@router.get("/online-users")
async def get_online_users_endpoint():
    """
    获取所有在线用户ID列表
    """
    online_users = manager.get_online_users()
    return {"online_users": online_users}

