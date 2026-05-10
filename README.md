# 聊天室应用（ChatRoomApp）

## 项目简介

这是一个前后端分离的聊天室应用，支持 **群聊** 与 **私聊**，并使用 **WebSocket** 实现实时消息推送。

## 🛠️ 技术栈

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Python FastAPI + SQLAlchemy
- **DB**: SQLite（数据持久化到 Docker Volume）

## 🚀 快速启动 (Docker)

### 前置要求

- 确保 Docker Desktop 已安装并运行

### 启动步骤

1. 在项目根目录执行：
```bash
docker compose up --build
```

2. 等待构建完成后，访问：
   - **前端**: http://localhost:3000
   - **后端 API 文档**: http://localhost:8000/docs
   - **健康检查**: http://localhost:8000/api/health

### 端口映射

- **前端**: 容器端口 80 → 宿主机端口 `3000`
- **后端**: 容器端口 8000 → 宿主机端口 `8000`

### 数据持久化

- SQLite 数据库文件存储在 `backend/database/` 目录
- 使用 Docker Volume 挂载，确保重启容器数据不丢失

### 停止服务

```bash
docker compose down
```

## 💻 本地开发启动（可选）

如果需要本地开发，可以按以下方式启动：

### 1) 启动后端

```bash
cd backend
copy env.example .env
py run.py
```

后端地址：
- API：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/health`

### 2) 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：`http://localhost:5173`

可选：创建 `frontend/.env` 指定后端地址：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 🧪 测试账号

本项目开放注册，请在启动后访问前端页面注册任意账号即可登录。

## 🗃️ 功能介绍

### 核心功能

- **账户系统**：注册 / 登录（JWT），密码 bcrypt 加密存储
- **群聊**：创建聊天室、加入/离开、历史消息
- **私聊**：会话列表、历史消息、已读/未读状态
- **在线用户**：查询在线用户 ID 列表
- **实时通信**：WebSocket（自动重连 / 心跳由前端实现）

## 目录结构（关键部分）

```
chatRoomApp/
├── backend/                 # FastAPI 后端
│   └── app/
│       ├── api/             # auth/chat 路由
│       ├── models/          # user/chat 模型
│       ├── services/        # auth/chat 业务逻辑
│       └── websocket/       # WebSocket 处理
└── frontend/                # React + TS + Tailwind 前端
    └── src/
        ├── pages/           # 登录/注册/聊天页面
        ├── components/      # Layout + Chat 组件
        ├── contexts/        # Auth/WebSocket 上下文
        └── services/        # auth/chat API 封装
```

## 作者

jiajing(jiajing@163.com)

