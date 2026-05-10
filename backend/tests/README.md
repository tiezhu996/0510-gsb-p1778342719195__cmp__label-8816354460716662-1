# 测试说明

## 修订历史

- **v1** (2026-01-19) - jiajing(jiajing@163.com) - 收敛为聊天室应用后，更新测试说明文档

## 测试框架

本项目使用 `pytest` 作为测试框架，配合 `pytest-asyncio` 和 `httpx` 进行异步和HTTP测试。

## 安装测试依赖

```bash
# 激活虚拟环境后
pip install -r requirements.txt
```

测试依赖包括：
- pytest==7.4.3
- pytest-asyncio==0.21.1
- httpx==0.25.2

## 运行测试

### 运行所有测试

```bash
# 在backend目录下
pytest tests/ -v
```

### 运行特定测试文件

```bash
# 运行认证功能测试
pytest tests/test_auth.py -v

# 运行API集成测试
pytest tests/test_auth_api.py -v
```

### 运行特定测试类或测试函数

```bash
# 运行特定测试类
pytest tests/test_auth.py::TestUserRegistration -v

# 运行特定测试函数
pytest tests/test_auth.py::TestUserRegistration::test_register_user_success -v
```

## 测试结构

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest配置和fixtures
│   ├── test_auth.py         # 认证功能单元测试
│   ├── test_auth_api.py     # 认证API集成测试
│   └── test_chat_api.py     # 聊天API集成测试
└── pytest.ini               # pytest配置文件
```

## 测试覆盖

### 单元测试 (test_auth.py)

1. **用户注册功能测试**
   - 成功注册新用户
   - 重复用户名注册
   - 重复邮箱注册

2. **用户登录功能测试**
   - 使用用户名成功登录
   - 使用邮箱成功登录
   - 错误用户名登录
   - 错误密码登录
   - 未激活用户登录

3. **JWT Token测试**
   - Token创建成功
   - Token包含用户信息
   - Token过期时间验证
   - 无效Token解码
   - 过期Token解码

### API集成测试 (test_auth_api.py)

1. **注册API测试**
   - 成功注册
   - 重复用户名
   - 重复邮箱
   - 无效数据验证

2. **登录API测试**
   - 使用用户名登录
   - 使用邮箱登录
   - 错误用户名
   - 错误密码

3. **用户信息API测试**
   - 获取当前用户信息（有效Token）
   - 无Token访问
   - 无效Token访问

4. **登出API测试**
   - 成功登出

## 测试数据库

测试使用SQLite内存数据库（`:memory:`），每个测试函数都会：
1. 创建新的数据库表
2. 执行测试
3. 清理数据库表

这确保了测试之间的隔离性。

## 注意事项

1. 测试不会影响开发数据库
2. 每个测试都是独立的，不会相互影响
3. 测试使用FastAPI的TestClient，不需要启动实际服务器

