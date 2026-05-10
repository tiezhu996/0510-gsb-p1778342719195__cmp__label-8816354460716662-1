"""
WebSocket处理器
处理WebSocket连接和消息
"""
import json
import logging
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from app.websocket.connection_manager import manager
from app.services.chat_service import (
    create_chat_message,
    create_private_message,
    get_chat_room,
    join_chat_room as join_room_service,
    leave_chat_room as leave_room_service
)
from app.utils.security import decode_access_token
from app.database import SessionLocal

logger = logging.getLogger(__name__)


async def verify_websocket_token(token: str) -> Optional[int]:
    """
    验证WebSocket连接的Token
    
    Args:
        token: JWT Token
        
    Returns:
        Optional[int]: 如果验证成功返回用户ID，否则返回None
    """
    try:
        if not token:
            logger.warning("Token为空")
            return None
            
        payload = decode_access_token(token)
        if payload is None:
            logger.warning("Token解码失败，payload为None")
            return None
            
        # sub可能是字符串或整数，需要处理
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            logger.warning("Token payload中缺少sub字段")
            return None
            
        try:
            # 转换为整数
            user_id = int(user_id_raw)
            logger.info(f"Token验证成功，用户ID: {user_id}")
            return user_id
        except (ValueError, TypeError) as e:
            logger.error(f"用户ID转换失败: {user_id_raw}, 错误: {e}")
            return None
    except Exception as e:
        logger.error(f"Token验证失败，异常: {e}", exc_info=True)
        return None


async def websocket_endpoint(websocket: WebSocket, user_id: int, token: str):
    """
    WebSocket端点处理函数
    
    Args:
        websocket: WebSocket连接对象
        user_id: 用户ID（从URL路径获取）
        token: JWT Token（从查询参数获取）
    """
    # 先接受连接，这样才能发送错误消息
    try:
        await websocket.accept()
    except Exception as e:
        logger.error(f"接受WebSocket连接失败: {e}")
        return
    
    # 验证Token
    verified_user_id = await verify_websocket_token(token)
    if not verified_user_id:
        logger.warning(f"WebSocket连接Token验证失败：token无效或为空")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token验证失败")
        return
        
    if verified_user_id != user_id:
        logger.warning(f"用户ID不匹配：URL中的user_id={user_id}，Token中的user_id={verified_user_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="用户ID不匹配")
        return
    
    # 建立连接（websocket已经accept了，只需要添加到管理器）
    # 注意：manager.connect 会再次调用 accept，所以我们需要直接添加到管理器
    manager.active_connections[user_id] = websocket
    if user_id not in manager.user_rooms:
        manager.user_rooms[user_id] = set()
    logger.info(f"用户 {user_id} 已连接WebSocket")
    
    # 创建数据库会话
    db: Session = SessionLocal()
    
    try:
        # 发送连接成功消息
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "user_id": user_id
        }, user_id)
        
        # 消息处理循环
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "chat_message":
                    # 处理群聊消息
                    await handle_chat_message(db, user_id, message)
                elif message_type == "private_message":
                    # 处理私聊消息
                    await handle_private_message(db, user_id, message)
                elif message_type == "join_room":
                    # 处理加入房间
                    await handle_join_room(db, user_id, message)
                elif message_type == "leave_room":
                    # 处理离开房间
                    await handle_leave_room(db, user_id, message)
                elif message_type == "ping":
                    # 心跳检测
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, user_id)
                else:
                    logger.warning(f"未知的消息类型: {message_type}")
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"未知的消息类型: {message_type}"
                    }, user_id)
                    
            except json.JSONDecodeError:
                logger.error(f"无效的JSON消息: {data}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "无效的消息格式"
                }, user_id)
            except Exception as e:
                logger.error(f"处理消息时出错: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "处理消息时出错"
                }, user_id)
                
    except WebSocketDisconnect:
        logger.info(f"用户 {user_id} WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        # 清理连接
        manager.disconnect(user_id)
        db.close()


async def handle_chat_message(db: Session, user_id: int, message: dict):
    """
    处理群聊消息
    
    Args:
        db: 数据库会话
        user_id: 发送者用户ID
        message: 消息字典
    """
    room_id = message.get("room_id")
    content = message.get("content")
    message_type = message.get("message_type", "text")
    
    if not room_id or not content:
        await manager.send_personal_message({
            "type": "error",
            "message": "缺少必要参数：room_id 或 content"
        }, user_id)
        return
    
    try:
        # 创建消息并保存到数据库
        chat_message = create_chat_message(db, room_id, user_id, content, message_type)
        
        # 刷新消息对象以加载关系（sender）
        db.refresh(chat_message)
        
        # 构建响应消息（包含发送者用户名）
        response_message = {
            "type": "chat_message",
            "id": chat_message.id,
            "room_id": room_id,
            "sender_id": user_id,
            "content": content,
            "message_type": message_type,
            "created_at": chat_message.created_at.isoformat(),
            "sender_username": chat_message.sender.username if chat_message.sender else None
        }
        
        # 向房间内所有用户广播消息（排除发送者）
        await manager.broadcast_to_room(response_message, room_id, exclude_user_id=user_id)
        
        # 向发送者发送完整的消息（让他也能实时看到自己发送的消息）
        await manager.send_personal_message(response_message, user_id)
        
    except HTTPException as e:
        await manager.send_personal_message({
            "type": "error",
            "message": e.detail
        }, user_id)
    except Exception as e:
        logger.error(f"处理群聊消息时出错: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "发送消息失败"
        }, user_id)


async def handle_private_message(db: Session, user_id: int, message: dict):
    """
    处理私聊消息
    
    Args:
        db: 数据库会话
        user_id: 发送者用户ID
        message: 消息字典
    """
    receiver_id = message.get("receiver_id")
    content = message.get("content")
    message_type = message.get("message_type", "text")
    
    if not receiver_id or not content:
        await manager.send_personal_message({
            "type": "error",
            "message": "缺少必要参数：receiver_id 或 content"
        }, user_id)
        return
    
    try:
        # 创建消息并保存到数据库
        private_message = create_private_message(db, user_id, receiver_id, content, message_type)
        
        # 刷新消息对象以加载关系（sender和receiver）
        db.refresh(private_message)
        
        # 构建响应消息（包含发送者和接收者用户名）
        response_message = {
            "type": "private_message",
            "id": private_message.id,
            "sender_id": user_id,
            "receiver_id": receiver_id,
            "content": content,
            "message_type": message_type,
            "is_read": False,
            "created_at": private_message.created_at.isoformat(),
            "sender_username": private_message.sender.username if private_message.sender else None,
            "receiver_username": private_message.receiver.username if private_message.receiver else None
        }
        
        # 向接收者发送消息
        await manager.send_personal_message(response_message, receiver_id)
        
        # 向发送者发送完整的消息（让他也能实时看到自己发送的消息）
        await manager.send_personal_message(response_message, user_id)
        
    except HTTPException as e:
        await manager.send_personal_message({
            "type": "error",
            "message": e.detail
        }, user_id)
    except Exception as e:
        logger.error(f"处理私聊消息时出错: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "发送消息失败"
        }, user_id)


async def handle_join_room(db: Session, user_id: int, message: dict):
    """
    处理加入房间
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        message: 消息字典
    """
    room_id = message.get("room_id")
    
    if not room_id:
        await manager.send_personal_message({
            "type": "error",
            "message": "缺少必要参数：room_id"
        }, user_id)
        return
    
    try:
        # 检查房间是否存在
        room = get_chat_room(db, room_id)
        if not room:
            await manager.send_personal_message({
                "type": "error",
                "message": "聊天室不存在"
            }, user_id)
            return
        
        # 加入房间（数据库）
        join_room_service(db, room_id, user_id)
        
        # 加入房间（WebSocket管理器）
        manager.join_room(user_id, room_id)
        
        # 发送确认消息
        await manager.send_personal_message({
            "type": "room_joined",
            "room_id": room_id,
            "room_name": room.name
        }, user_id)
        
        # 通知房间内其他用户
        await manager.broadcast_to_room({
            "type": "user_joined",
            "room_id": room_id,
            "user_id": user_id
        }, room_id, exclude_user_id=user_id)
        
    except HTTPException as e:
        await manager.send_personal_message({
            "type": "error",
            "message": e.detail
        }, user_id)
    except Exception as e:
        logger.error(f"处理加入房间时出错: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "加入房间失败"
        }, user_id)


async def handle_leave_room(db: Session, user_id: int, message: dict):
    """
    处理离开房间
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        message: 消息字典
    """
    room_id = message.get("room_id")
    
    if not room_id:
        await manager.send_personal_message({
            "type": "error",
            "message": "缺少必要参数：room_id"
        }, user_id)
        return
    
    try:
        # 离开房间（仅从WebSocket管理器移除，不从数据库移除成员身份）
        # leave_room_service(db, room_id, user_id)
        
        # 离开房间（WebSocket管理器）
        manager.leave_room(user_id, room_id)
        
        # 发送确认消息
        await manager.send_personal_message({
            "type": "room_left",
            "room_id": room_id
        }, user_id)
        
        # 通知房间内其他用户
        await manager.broadcast_to_room({
            "type": "user_left",
            "room_id": room_id,
            "user_id": user_id
        }, room_id, exclude_user_id=user_id)
        
    except HTTPException as e:
        await manager.send_personal_message({
            "type": "error",
            "message": e.detail
        }, user_id)
    except Exception as e:
        logger.error(f"处理离开房间时出错: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "离开房间失败"
        }, user_id)

