"""
认证API端点集成测试
测试认证相关的HTTP API接口
"""
import pytest
from fastapi import status


class TestAuthAPI:
    """认证API测试"""
    
    def test_register_api_success(self, client):
        """测试注册API成功"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "password" not in data  # 密码不应该返回
        assert "hashed_password" not in data  # 密码哈希不应该返回
    
    def test_register_api_duplicate_username(self, client):
        """测试注册API重复用户名"""
        # 先注册一个用户
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "password123"
            }
        )
        
        # 尝试用相同用户名注册
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "用户名已存在" in response.json()["detail"]
    
    def test_register_api_duplicate_email(self, client):
        """测试注册API重复邮箱"""
        # 先注册一个用户
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser1",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # 尝试用相同邮箱注册
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser2",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "邮箱已被注册" in response.json()["detail"]
    
    def test_register_api_invalid_data(self, client):
        """测试注册API无效数据"""
        # 测试密码太短
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "12345"  # 少于6个字符
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # 测试无效邮箱
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_api_success_with_username(self, client):
        """测试登录API成功（使用用户名）"""
        # 先注册用户
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # 登录
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert len(data["access_token"]) > 0
    
    def test_login_api_success_with_email(self, client):
        """测试登录API成功（使用邮箱）"""
        # 先注册用户
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # 使用邮箱登录
        response = client.post(
            "/api/auth/login",
            json={
                "username": "test@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_api_wrong_username(self, client):
        """测试登录API错误用户名"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "用户名或密码错误" in response.json()["detail"]
    
    def test_login_api_wrong_password(self, client):
        """测试登录API错误密码"""
        # 先注册用户
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # 使用错误密码登录
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "用户名或密码错误" in response.json()["detail"]
    
    def test_get_current_user_api_success(self, client):
        """测试获取当前用户信息API成功"""
        # 先注册并登录
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        assert "access_token" in login_data
        token = login_data["access_token"]
        
        # 获取当前用户信息
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_get_current_user_api_no_token(self, client):
        """测试获取当前用户信息API无Token"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_api_invalid_token(self, client):
        """测试获取当前用户信息API无效Token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_api_success(self, client):
        """测试登出API成功"""
        # 先注册并登录
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        assert "access_token" in login_data
        token = login_data["access_token"]
        
        # 登出
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "成功登出" in response.json()["message"]

