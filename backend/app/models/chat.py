"""
聊天相关模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Table, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

# 聊天室成员关联表（多对多关系）
room_members = Table(
    'room_members',
    Base.metadata,
    Column('room_id', Integer, ForeignKey('chat_rooms.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('joined_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
    Index('idx_room_member_room', 'room_id'),
    Index('idx_room_member_user', 'user_id'),
)


class ChatRoom(Base):
    """聊天室模型"""
    __tablename__ = "chat_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_public = Column(Boolean, default=True, nullable=False)  # 是否公开聊天室
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 定义关系
    creator = relationship("User", backref="created_chat_rooms")
    members = relationship("User", secondary=room_members, backref="joined_chat_rooms")
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")
    
    # 定义索引
    __table_args__ = (
        Index('idx_chat_room_name', 'name'),
        Index('idx_chat_room_creator', 'creator_id'),
    )
    
    def __repr__(self):
        return f"<ChatRoom(id={self.id}, name='{self.name}')>"


class ChatMessage(Base):
    """群聊消息模型"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text", nullable=False)  # text, image, file等
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # 定义关系
    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", backref="chat_messages")
    
    # 定义索引
    __table_args__ = (
        Index('idx_chat_message_room', 'room_id'),
        Index('idx_chat_message_sender', 'sender_id'),
        Index('idx_chat_message_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, room_id={self.room_id}, sender_id={self.sender_id})>"


class PrivateMessage(Base):
    """私聊消息模型"""
    __tablename__ = "private_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text", nullable=False)  # text, image, file等
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # 定义关系
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_private_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_private_messages")
    
    # 定义索引
    __table_args__ = (
        Index('idx_private_message_sender', 'sender_id'),
        Index('idx_private_message_receiver', 'receiver_id'),
        Index('idx_private_message_created', 'created_at'),
        Index('idx_private_message_read', 'is_read'),
    )
    
    def __repr__(self):
        return f"<PrivateMessage(id={self.id}, sender_id={self.sender_id}, receiver_id={self.receiver_id})>"

