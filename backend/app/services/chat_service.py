"""
聊天服务
处理聊天相关的业务逻辑
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, select
from fastapi import HTTPException, status
from app.models.chat import ChatRoom, ChatMessage, PrivateMessage, room_members
from app.models.user import User
from app.schemas.chat import ChatRoomCreate


# ========== 聊天室相关 ==========

def create_chat_room(db: Session, room_create: ChatRoomCreate, creator_id: int) -> ChatRoom:
    """
    创建聊天室
    
    Args:
        db: 数据库会话
        room_create: 聊天室创建数据
        creator_id: 创建者ID
        
    Returns:
        ChatRoom: 创建的聊天室对象
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"开始创建聊天室: name={room_create.name}, is_public={room_create.is_public}, creator_id={creator_id}")
    
    chat_room = ChatRoom(
        name=room_create.name,
        description=room_create.description,
        creator_id=creator_id,
        is_public=room_create.is_public
    )
    
    db.add(chat_room)
    db.flush()  # 获取room.id
    logger.info(f"聊天室已创建: room_id={chat_room.id}")
    
    # 创建者自动加入聊天室
    logger.info(f"准备将创建者加入聊天室: room_id={chat_room.id}, user_id={creator_id}")
    try:
        db.execute(
            room_members.insert().values(room_id=chat_room.id, user_id=creator_id)
        )
        db.flush()  # 确保插入被执行
        logger.info(f"创建者已加入聊天室成员表")
    except Exception as e:
        logger.error(f"加入聊天室成员表失败: {e}")
        raise
    
    # 立即提交事务，确保数据被保存
    db.commit()
    logger.info(f"✅ 事务已提交到数据库")
    
    # 重新查询以验证（在新的事务中）
    from sqlalchemy import select, and_, text
    check_result = db.execute(
        text("SELECT * FROM room_members WHERE room_id=:room_id AND user_id=:user_id"),
        {"room_id": chat_room.id, "user_id": creator_id}
    ).first()
    logger.info(f"✅ 数据库验证: room_id={chat_room.id}, user_id={creator_id}, 存在={check_result is not None}")
    
    return chat_room


def delete_chat_room(db: Session, room_id: int, user_id: int) -> bool:
    """
    删除聊天室
    
    Args:
        db: 数据库会话
        room_id: 聊天室ID
        user_id: 请求用户ID (必须是创建者)
        
    Returns:
        bool: 如果删除成功返回True
        
    Raises:
        HTTPException: 如果聊天室不存在或用户不是创建者
    """
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )
        
    if room.creator_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有创建者可以删除聊天室"
        )
    
    # 删除群聊成员
    db.execute(
        room_members.delete().where(room_members.c.room_id == room_id)
    )
    
    # 删除群聊消息
    db.query(ChatMessage).filter(ChatMessage.room_id == room_id).delete()
    
    # 删除聊天室
    db.delete(room)
    db.commit()
    
    return True


def invite_user_to_room(db: Session, room_id: int, inviter_id: int, username: str) -> User:
    """
    邀请用户加入聊天室
    
    Args:
        db: 数据库会话
        room_id: 聊天室ID
        inviter_id: 邀请人ID (必须是创建者)
        username: 被邀请用户名
        
    Returns:
        User: 被邀请的用户对象
        
    Raises:
        HTTPException: 
            - 404: 聊天室不存在或用户不存在
            - 403: 邀请人不是创建者
    """
    # 1. 检查聊天室
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )
        
    # 2. 检查权限 (必须是创建者)
    if room.creator_id != inviter_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有创建者可以邀请用户"
        )
        
    # 3. 检查被邀请用户
    invitee = db.query(User).filter(User.username == username).first()
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 '{username}' 不存在"
        )
        
    # 4. 检查是否已在聊天室
    existing = db.execute(
        select(room_members).where(
            and_(room_members.c.room_id == room_id, room_members.c.user_id == invitee.id)
        )
    ).first()
    
    if existing:
        return invitee
        
    # 5. 添加成员
    db.execute(
        room_members.insert().values(room_id=room_id, user_id=invitee.id)
    )
    db.commit()
    
    return invitee


def get_chat_room(db: Session, room_id: int) -> Optional[ChatRoom]:
    """
    根据ID获取聊天室
    
    Args:
        db: 数据库会话
        room_id: 聊天室ID
        
    Returns:
        ChatRoom: 聊天室对象，如果不存在返回None
    """
    return db.query(ChatRoom).filter(ChatRoom.id == room_id).first()


def get_chat_rooms(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[int] = None,
    is_public: Optional[bool] = None,
    current_user_id: Optional[int] = None
) -> tuple[List[ChatRoom], int]:
    """
    获取聊天室列表（支持分页、按用户筛选）
    
    可见性规则：
    - 公开聊天室（is_public=True）：所有人可见
    - 非公开聊天室（is_public=False）：只有成员可见
    
    Args:
        db: 数据库会话
        page: 页码（从1开始）
        page_size: 每页数量
        user_id: 用户ID（可选，用于筛选用户加入的聊天室）
        is_public: 是否公开（可选，用于筛选公开/私有聊天室）
        current_user_id: 当前用户ID（可选，用于权限控制）
        
    Returns:
        tuple: (聊天室列表, 总数)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"get_chat_rooms called: page={page}, page_size={page_size}, user_id={user_id}, is_public={is_public}, current_user_id={current_user_id}")
    
    query = db.query(ChatRoom)
    
    # 按用户筛选（用户加入的聊天室）
    if user_id is not None:
        logger.info(f"Filtering by user_id={user_id}")
        query = query.join(room_members).filter(room_members.c.user_id == user_id)
    
    # 按是否公开筛选
    if is_public is not None:
        logger.info(f"Filtering by is_public={is_public}")
        query = query.filter(ChatRoom.is_public == is_public)
    else:
        # 如果没有指定 is_public，应用可见性规则
        if current_user_id is not None:
            logger.info(f"Applying visibility rules for logged-in user: current_user_id={current_user_id}")
            # 已登录用户：显示所有公开聊天室 + 用户加入的非公开聊天室
            # 构建子查询：用户加入的聊天室ID列表
            user_rooms_subquery = db.query(room_members.c.room_id).filter(
                room_members.c.user_id == current_user_id
            ).subquery()
            
            # 调试：查看用户加入的聊天室ID
            user_room_ids = db.query(room_members.c.room_id).filter(
                room_members.c.user_id == current_user_id
            ).all()
            logger.info(f"User {current_user_id} joined rooms: {[r[0] for r in user_room_ids]}")
            
            # 应用OR条件：
            # 1. 公开聊天室
            # 2. 用户已加入的聊天室 (room_members表)
            # 3. 用户创建的聊天室 (creator_id字段 - 作为兜底)
            query = query.filter(
                or_(
                    ChatRoom.is_public == True,
                    ChatRoom.id.in_(select(user_rooms_subquery)),
                    ChatRoom.creator_id == current_user_id
                )
            )
        else:
            logger.info("No current_user_id, showing only public rooms")
            # 未登录用户：只显示公开聊天室
            query = query.filter(ChatRoom.is_public == True)
    
    # 获取总数
    total = query.count()
    logger.info(f"Total rooms matching criteria: {total}")
    
    # 排序：按创建时间倒序
    query = query.order_by(ChatRoom.created_at.desc())
    
    # 分页
    offset = (page - 1) * page_size
    rooms = query.offset(offset).limit(page_size).all()
    
    logger.info(f"Returning {len(rooms)} rooms for page {page}")
    for room in rooms:
        logger.info(f"  Room: id={room.id}, name={room.name}, is_public={room.is_public}, creator_id={room.creator_id}")
    
    return rooms, total


def join_chat_room(db: Session, room_id: int, user_id: int) -> bool:
    """
    加入聊天室
    
    Args:
        db: 数据库会话
        room_id: 聊天室ID
        user_id: 用户ID
        
    Returns:
        bool: 如果加入成功返回True
        
    Raises:
        HTTPException: 如果聊天室不存在或用户已在聊天室中
    """
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )
    
    # 检查用户是否已在聊天室中
    existing = db.execute(
        select(room_members).where(
            and_(room_members.c.room_id == room_id, room_members.c.user_id == user_id)
        )
    ).first()
    
    if existing:
        # 用户已在聊天室中，直接返回成功（创建者会自动加入）
        return True
    
    # 加入聊天室
    db.execute(
        room_members.insert().values(room_id=room_id, user_id=user_id)
    )
    db.commit()
    
    return True


def leave_chat_room(db: Session, room_id: int, user_id: int) -> bool:
    """
    离开聊天室
    
    Args:
        db: 数据库会话
        room_id: 聊天室ID
        user_id: 用户ID
        
    Returns:
        bool: 如果离开成功返回True
        
    Raises:
        HTTPException: 如果聊天室不存在或用户不在聊天室中
    """
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )
    
    # 检查用户是否在聊天室中
    existing = db.execute(
        select(room_members).where(
            and_(room_members.c.room_id == room_id, room_members.c.user_id == user_id)
        )
    ).first()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户不在聊天室中"
        )
    
    # 离开聊天室
    db.execute(
        room_members.delete().where(
            and_(room_members.c.room_id == room_id, room_members.c.user_id == user_id)
        )
    )
    db.commit()
    
    return True


def get_room_member_count(db: Session, room_id: int) -> int:
    """
    获取聊天室成员数量
    
    Args:
        db: 数据库会话
        room_id: 聊天室ID
        
    Returns:
        int: 成员数量
    """
    result = db.execute(
        select(func.count(room_members.c.user_id)).where(room_members.c.room_id == room_id)
    ).scalar()
    return result or 0


# ========== 群聊消息相关 ==========

def create_chat_message(
    db: Session,
    room_id: int,
    sender_id: int,
    content: str,
    message_type: str = "text"
) -> ChatMessage:
    """
    创建群聊消息
    
    Args:
        db: 数据库会话
        room_id: 聊天室ID
        sender_id: 发送者ID
        content: 消息内容
        message_type: 消息类型
        
    Returns:
        ChatMessage: 创建的消息对象
        
    Raises:
        HTTPException: 如果聊天室不存在或用户不在聊天室中
    """
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )
    
    # 检查用户是否在聊天室中
    existing = db.execute(
        select(room_members).where(
            and_(room_members.c.room_id == room_id, room_members.c.user_id == sender_id)
        )
    ).first()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户不在聊天室中，无法发送消息"
        )
    
    message = ChatMessage(
        room_id=room_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message


def get_chat_messages(
    db: Session,
    room_id: int,
    page: int = 1,
    page_size: int = 50
) -> tuple[List[ChatMessage], int]:
    """
    获取聊天室消息历史（分页）
    
    Args:
        db: 数据库会话
        room_id: 聊天室ID
        page: 页码（从1开始）
        page_size: 每页数量
        
    Returns:
        tuple: (消息列表, 总数)
    """
    query = db.query(ChatMessage).filter(ChatMessage.room_id == room_id)
    
    # 获取总数
    total = query.count()
    
    # 排序：按创建时间倒序（最新的在前）
    query = query.order_by(desc(ChatMessage.created_at))
    
    # 分页
    offset = (page - 1) * page_size
    messages = query.offset(offset).limit(page_size).all()
    
    # 反转列表，使最旧的消息在前（用于前端显示）
    messages.reverse()
    
    return messages, total


# ========== 私聊消息相关 ==========

def create_private_message(
    db: Session,
    sender_id: int,
    receiver_id: int,
    content: str,
    message_type: str = "text"
) -> PrivateMessage:
    """
    创建私聊消息
    
    Args:
        db: 数据库会话
        sender_id: 发送者ID
        receiver_id: 接收者ID
        content: 消息内容
        message_type: 消息类型
        
    Returns:
        PrivateMessage: 创建的消息对象
        
    Raises:
        HTTPException: 如果接收者不存在
    """
    # 检查接收者是否存在
    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接收者不存在"
        )
    
    if sender_id == receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能给自己发送私聊消息"
        )
    
    message = PrivateMessage(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        message_type=message_type
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message


def get_private_messages(
    db: Session,
    user1_id: int,
    user2_id: int,
    page: int = 1,
    page_size: int = 50
) -> tuple[List[PrivateMessage], int]:
    """
    获取两个用户之间的私聊消息历史（分页）
    
    Args:
        db: 数据库会话
        user1_id: 用户1 ID
        user2_id: 用户2 ID
        page: 页码（从1开始）
        page_size: 每页数量
        
    Returns:
        tuple: (消息列表, 总数)
    """
    query = db.query(PrivateMessage).filter(
        or_(
            and_(PrivateMessage.sender_id == user1_id, PrivateMessage.receiver_id == user2_id),
            and_(PrivateMessage.sender_id == user2_id, PrivateMessage.receiver_id == user1_id)
        )
    )
    
    # 获取总数
    total = query.count()
    
    # 排序：按创建时间倒序（最新的在前）
    query = query.order_by(desc(PrivateMessage.created_at))
    
    # 分页
    offset = (page - 1) * page_size
    messages = query.offset(offset).limit(page_size).all()
    
    # 反转列表，使最旧的消息在前（用于前端显示）
    messages.reverse()
    
    return messages, total


def get_user_conversations(db: Session, user_id: int) -> List[dict]:
    """
    获取用户的私聊会话列表
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        List[dict]: 会话列表，每个会话包含对方用户信息和最后一条消息
    """
    # 使用更高效的查询：直接获取所有有消息往来的对方用户ID（不加载所有消息）
    # 获取作为发送者的对方用户ID
    sent_user_ids = db.query(PrivateMessage.receiver_id).filter(
        PrivateMessage.sender_id == user_id
    ).distinct().all()
    
    # 获取作为接收者的对方用户ID
    received_user_ids = db.query(PrivateMessage.sender_id).filter(
        PrivateMessage.receiver_id == user_id
    ).distinct().all()
    
    # 合并并去重
    other_user_ids = set()
    for row in sent_user_ids:
        other_user_ids.add(row[0])
    for row in received_user_ids:
        other_user_ids.add(row[0])
    
    if not other_user_ids:
        return []
    
    # 为每个对方用户获取最后一条消息和相关信息
    conversations = []
    for other_user_id in other_user_ids:
        # 获取最后一条消息（使用 joinedload 预加载关系以提高性能）
        last_message = db.query(PrivateMessage).options(
            joinedload(PrivateMessage.sender),
            joinedload(PrivateMessage.receiver)
        ).filter(
            or_(
                and_(PrivateMessage.sender_id == user_id, PrivateMessage.receiver_id == other_user_id),
                and_(PrivateMessage.sender_id == other_user_id, PrivateMessage.receiver_id == user_id)
            )
        ).order_by(desc(PrivateMessage.created_at)).first()
        
        # 如果没有找到消息，跳过（理论上不应该发生，因为我们是从消息中获取的用户ID）
        if not last_message:
            continue
        
        # 获取未读消息数量
        unread_count = db.query(PrivateMessage).filter(
            and_(
                PrivateMessage.sender_id == other_user_id,
                PrivateMessage.receiver_id == user_id,
                PrivateMessage.is_read == False
            )
        ).count()
        
        # 获取对方用户信息
        other_user = db.query(User).filter(User.id == other_user_id).first()
        
        if other_user:
            conversations.append({
                'user_id': other_user_id,
                'username': other_user.username,
                'last_message': last_message,
                'unread_count': unread_count,
                'last_message_at': last_message.created_at
            })
    
    # 按最后消息时间排序
    conversations.sort(key=lambda x: x['last_message_at'], reverse=True)
    
    return conversations


def mark_message_read(db: Session, message_id: int, user_id: int) -> bool:
    """
    标记私聊消息为已读
    
    Args:
        db: 数据库会话
        message_id: 消息ID
        user_id: 用户ID（接收者）
        
    Returns:
        bool: 如果标记成功返回True
        
    Raises:
        HTTPException: 如果消息不存在或用户不是接收者
    """
    message = db.query(PrivateMessage).filter(PrivateMessage.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    if message.receiver_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权标记此消息为已读"
        )
    
    if not message.is_read:
        message.is_read = True
        from datetime import datetime
        from sqlalchemy.sql import func
        message.read_at = func.now()
        db.commit()
    
    return True


def get_unread_count(db: Session, user_id: int, sender_id: Optional[int] = None) -> int:
    """
    获取用户的未读消息数量
    
    Args:
        db: 数据库会话
        user_id: 用户ID（接收者）
        sender_id: 发送者ID（可选，用于获取特定发送者的未读消息数）
        
    Returns:
        int: 未读消息数量
    """
    query = db.query(PrivateMessage).filter(
        and_(
            PrivateMessage.receiver_id == user_id,
            PrivateMessage.is_read == False
        )
    )
    
    if sender_id:
        query = query.filter(PrivateMessage.sender_id == sender_id)
    
    return query.count()

