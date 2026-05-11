"""
聊天API端点集成测试
测试聊天相关的HTTP API接口
"""
import pytest
from fastapi import status


class TestChatAPI:
    """聊天API测试"""
    
    def test_create_chat_room_success(self, client, auth_headers):
        """测试创建聊天室成功"""
        headers = auth_headers()
        
        response = client.post(
            "/api/chat/rooms",
            json={
                "name": "测试聊天室",
                "description": "这是一个测试聊天室",
                "is_public": True
            },
            headers=headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == "测试聊天室"
        assert data["description"] == "这是一个测试聊天室"
        assert data["is_public"] is True
        assert "creator_id" in data
        assert "member_count" in data
        assert data["member_count"] >= 1  # 创建者自动加入
    
    def test_create_chat_room_no_auth(self, client):
        """测试未登录创建聊天室（应失败）"""
        response = client.post(
            "/api/chat/rooms",
            json={
                "name": "测试聊天室",
                "is_public": True
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_chat_rooms_list(self, client, auth_headers):
        """测试获取聊天室列表"""
        headers = auth_headers()
        
        # 创建几个聊天室
        for i in range(3):
            client.post(
                "/api/chat/rooms",
                json={
                    "name": f"测试聊天室 {i+1}",
                    "is_public": True
                },
                headers=headers
            )
        
        response = client.get("/api/chat/rooms", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "rooms" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["rooms"]) >= 3
    
    def test_get_chat_room_detail(self, client, auth_headers):
        """测试获取聊天室详情"""
        headers = auth_headers()
        
        # 创建聊天室
        create_response = client.post(
            "/api/chat/rooms",
            json={
                "name": "测试聊天室",
                "is_public": True
            },
            headers=headers
        )
        room_id = create_response.json()["id"]
        
        response = client.get(f"/api/chat/rooms/{room_id}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == room_id
        assert data["name"] == "测试聊天室"
        assert "member_count" in data
    
    def test_get_chat_room_not_found(self, client, auth_headers):
        """测试获取不存在的聊天室（404）"""
        headers = auth_headers()
        
        response = client.get("/api/chat/rooms/99999", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_join_chat_room(self, client, auth_headers):
        """测试加入聊天室"""
        headers1 = auth_headers("user1", "password123")
        headers2 = auth_headers("user2", "password123")
        
        # 用户1创建聊天室
        create_response = client.post(
            "/api/chat/rooms",
            json={
                "name": "测试聊天室",
                "is_public": True
            },
            headers=headers1
        )
        room_id = create_response.json()["id"]
        
        # 用户2加入聊天室
        response = client.post(f"/api/chat/rooms/{room_id}/join", headers=headers2)
        
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()
    
    def test_join_chat_room_already_member(self, client, auth_headers):
        """测试加入已加入的聊天室（应失败）"""
        headers = auth_headers()
        
        # 创建聊天室（创建者自动加入）
        create_response = client.post(
            "/api/chat/rooms",
            json={
                "name": "测试聊天室",
                "is_public": True
            },
            headers=headers
        )
        room_id = create_response.json()["id"]
        
        # 再次尝试加入
        response = client.post(f"/api/chat/rooms/{room_id}/join", headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_leave_chat_room(self, client, auth_headers):
        """测试离开聊天室"""
        headers = auth_headers()
        
        # 创建聊天室
        create_response = client.post(
            "/api/chat/rooms",
            json={
                "name": "测试聊天室",
                "is_public": True
            },
            headers=headers
        )
        room_id = create_response.json()["id"]
        
        # 离开聊天室
        response = client.post(f"/api/chat/rooms/{room_id}/leave", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_leave_chat_room_not_member(self, client, auth_headers):
        """测试离开未加入的聊天室（应失败）"""
        headers1 = auth_headers("user1", "password123")
        headers2 = auth_headers("user2", "password123")
        
        # 用户1创建聊天室
        create_response = client.post(
            "/api/chat/rooms",
            json={
                "name": "测试聊天室",
                "is_public": True
            },
            headers=headers1
        )
        room_id = create_response.json()["id"]
        
        # 用户2尝试离开（未加入）
        response = client.post(f"/api/chat/rooms/{room_id}/leave", headers=headers2)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_chat_room_messages(self, client, auth_headers):
        """测试获取聊天室消息历史"""
        headers = auth_headers()
        
        # 创建聊天室
        create_response = client.post(
            "/api/chat/rooms",
            json={
                "name": "测试聊天室",
                "is_public": True
            },
            headers=headers
        )
        room_id = create_response.json()["id"]
        
        response = client.get(f"/api/chat/rooms/{room_id}/messages", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "messages" in data
        assert "page" in data
        assert "page_size" in data
    
    def test_get_private_conversations(self, client, auth_headers):
        """测试获取私聊会话列表"""
        headers = auth_headers()
        
        response = client.get("/api/chat/private/conversations", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
    
    def test_get_private_messages(self, client, auth_headers):
        """测试获取私聊消息历史"""
        headers1 = auth_headers("user1", "password123")
        headers2 = auth_headers("user2", "password123")
        
        # 获取用户ID
        user1_response = client.get("/api/auth/me", headers=headers1)
        user1_id = user1_response.json()["id"]
        
        user2_response = client.get("/api/auth/me", headers=headers2)
        user2_id = user2_response.json()["id"]
        
        # 获取私聊消息（即使没有消息也应该返回空列表）
        response = client.get(f"/api/chat/private/{user2_id}/messages", headers=headers1)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "messages" in data
        assert isinstance(data["messages"], list)
    
    def test_get_private_messages_self(self, client, auth_headers):
        """测试获取与自己的私聊消息（应失败）"""
        headers = auth_headers()
        
        # 获取当前用户ID
        user_response = client.get("/api/auth/me", headers=headers)
        user_id = user_response.json()["id"]
        
        response = client.get(f"/api/chat/private/{user_id}/messages", headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_unread_count(self, client, auth_headers):
        """测试获取未读消息数量"""
        headers = auth_headers()
        
        response = client.get("/api/chat/private/unread-count", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
        assert data["unread_count"] >= 0
    
    def test_get_online_users(self, client):
        """测试获取在线用户列表"""
        response = client.get("/api/chat/online-users")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "online_users" in data
        assert isinstance(data["online_users"], list)

