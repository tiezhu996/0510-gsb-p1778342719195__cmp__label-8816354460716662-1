"""
WebSocket连接管理器
管理WebSocket连接、房间和消息发送
"""
from typing import Dict, Set, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 用户ID -> WebSocket连接的映射
        self.active_connections: Dict[int, WebSocket] = {}
        # 房间ID -> 用户ID集合的映射
        self.rooms: Dict[int, Set[int]] = {}
        # 用户ID -> 房间ID集合的映射（用于快速查找用户所在的房间）
        self.user_rooms: Dict[int, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_rooms[user_id] = set()
        logger.info(f"用户 {user_id} 已连接WebSocket")
    
    def disconnect(self, user_id: int):
        """
        断开WebSocket连接
        
        Args:
            user_id: 用户ID
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"用户 {user_id} 已断开WebSocket连接")
        
        # 从所有房间中移除用户
        if user_id in self.user_rooms:
            rooms_to_leave = list(self.user_rooms[user_id])
            for room_id in rooms_to_leave:
                self.leave_room(user_id, room_id)
            del self.user_rooms[user_id]
    
    def is_connected(self, user_id: int) -> bool:
        """
        检查用户是否已连接
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 如果用户已连接返回True
        """
        return user_id in self.active_connections
    
    async def send_personal_message(self, message: dict, user_id: int):
        """
        发送个人消息（私聊）
        
        Args:
            message: 消息字典
            user_id: 接收者用户ID
        """
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(json.dumps(message))
                logger.debug(f"向用户 {user_id} 发送消息: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"向用户 {user_id} 发送消息失败: {e}")
                # 如果发送失败，移除连接
                self.disconnect(user_id)
        else:
            logger.debug(f"用户 {user_id} 未连接，无法发送消息")
    
    async def broadcast_to_room(self, message: dict, room_id: int, exclude_user_id: int = None):
        """
        向房间内所有用户广播消息（群聊）
        
        Args:
            message: 消息字典
            room_id: 房间ID
            exclude_user_id: 排除的用户ID（通常是发送者）
        """
        if room_id not in self.rooms:
            logger.warning(f"房间 {room_id} 不存在或没有成员")
            return
        
        disconnected_users = []
        for user_id in self.rooms[room_id]:
            # 排除发送者
            if exclude_user_id and user_id == exclude_user_id:
                continue
            
            if user_id in self.active_connections:
                try:
                    websocket = self.active_connections[user_id]
                    await websocket.send_text(json.dumps(message))
                    logger.debug(f"向房间 {room_id} 的用户 {user_id} 广播消息")
                except Exception as e:
                    logger.error(f"向用户 {user_id} 广播消息失败: {e}")
                    disconnected_users.append(user_id)
            else:
                logger.debug(f"用户 {user_id} 未连接，跳过广播")
        
        # 清理断开的连接
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    def join_room(self, user_id: int, room_id: int):
        """
        用户加入房间
        
        Args:
            user_id: 用户ID
            room_id: 房间ID
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(user_id)
        
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        
        self.user_rooms[user_id].add(room_id)
        logger.info(f"用户 {user_id} 加入房间 {room_id}")
    
    def leave_room(self, user_id: int, room_id: int):
        """
        用户离开房间
        
        Args:
            user_id: 用户ID
            room_id: 房间ID
        """
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
            # 如果房间为空，删除房间
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)
        
        logger.info(f"用户 {user_id} 离开房间 {room_id}")
    
    def get_room_members(self, room_id: int) -> List[int]:
        """
        获取房间内的所有用户ID
        
        Args:
            room_id: 房间ID
            
        Returns:
            List[int]: 用户ID列表
        """
        if room_id in self.rooms:
            return list(self.rooms[room_id])
        return []
    
    def get_online_users(self) -> List[int]:
        """
        获取所有在线用户ID
        
        Returns:
            List[int]: 在线用户ID列表
        """
        return list(self.active_connections.keys())
    
    def get_user_rooms(self, user_id: int) -> List[int]:
        """
        获取用户所在的所有房间ID
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[int]: 房间ID列表
        """
        if user_id in self.user_rooms:
            return list(self.user_rooms[user_id])
        return []


# 全局连接管理器实例
manager = ConnectionManager()

