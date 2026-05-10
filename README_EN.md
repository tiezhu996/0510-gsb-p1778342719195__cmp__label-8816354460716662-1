# ChatRoomApp

## Revision History

- **v2** (2026-01-19) - jiajing(jiajing@163.com) - Refocused to a chat-only app: Tailwind on frontend, backend keeps only auth + chat modules

## Overview

A full-stack chat application with **group chat** and **private chat**, using **WebSocket** for real-time messaging.

## Features

- **Auth**: Register / Login (JWT), bcrypt password hashing
- **Group Chat**: Create rooms, join/leave, paginated history
- **Private Chat**: Conversations list, paginated history, read/unread status
- **Online Users**: Query online user ID list
- **Realtime**: WebSocket messaging (reconnect/heartbeat handled in frontend)

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + SQLAlchemy
- **Database**: SQLite (default)

## Quick Start

### Backend

```bash
cd backend
copy env.example .env
py run.py
```

Backend URLs:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

Optional `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Author

jiajing(jiajing@163.com)

