"""
FastAPI应用入口文件
"""
from fastapi import FastAPI, WebSocket, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.api import auth, chat
from app.websocket.handlers import websocket_endpoint
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title="聊天室应用",
    description="支持群聊、私聊与WebSocket实时通信的聊天室应用",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS响应头中间件（确保所有响应都包含CORS头）
class CORSHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        response = await call_next(request)
        # 为所有响应添加CORS头
        response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
        return response

app.add_middleware(CORSHeaderMiddleware)

# 应用启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    from app.database import init_db
    from app.models import User, ChatRoom, ChatMessage, PrivateMessage  # noqa: F401
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

# 配置CORS中间件 - 必须在路由注册之前
# 开发环境使用更宽松的CORS配置
if settings.ENVIRONMENT == "development":
    # 开发环境：允许所有来源
    cors_origins = ["*"]
    logger.info("[CORS配置] 开发环境：允许所有来源")
else:
    # 生产环境：使用配置的来源列表
    cors_origins = settings.cors_origins_list if settings.cors_origins_list else ["http://localhost:5173", "http://localhost:3000"]
    logger.info(f"[CORS配置] 生产环境允许的来源: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
    expose_headers=["*"],  # 暴露所有响应头
    max_age=3600,
)

# 添加OPTIONS请求处理器（预检请求）
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """处理CORS预检请求"""
    origin = request.headers.get("origin")
    headers = {
        "Access-Control-Allow-Origin": origin if origin else "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Max-Age": "3600",
    }
    return JSONResponse(content={}, headers=headers)

# 添加ValidationError异常处理器
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """处理Pydantic验证错误"""
    import traceback
    logger.error(f"Pydantic验证错误: {exc}")
    logger.error(f"异常堆栈: {traceback.format_exc()}")
    origin = request.headers.get("origin")
    cors_headers = {
        "Access-Control-Allow-Origin": origin if origin else "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(
        status_code=500,
        content={"detail": f"数据验证错误: {str(exc)}", "errors": exc.errors() if hasattr(exc, 'errors') else []},
        headers=cors_headers
    )

# 添加RequestValidationError异常处理器
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    import traceback
    logger.error(f"请求验证错误: {exc}")
    logger.error(f"异常堆栈: {traceback.format_exc()}")
    origin = request.headers.get("origin")
    cors_headers = {
        "Access-Control-Allow-Origin": origin if origin else "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(
        status_code=422,
        content={"detail": "请求验证失败", "errors": exc.errors()},
        headers=cors_headers
    )

# 添加全局异常处理器，确保CORS头始终被添加
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，确保CORS头被添加"""
    import traceback
    logger.error(f"未处理的异常: {exc}")
    logger.error(f"异常类型: {type(exc).__name__}")
    logger.error(f"异常堆栈: {traceback.format_exc()}")
    origin = request.headers.get("origin")
    cors_headers = {
        "Access-Control-Allow-Origin": origin if origin else "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(
        status_code=500,
        content={"detail": f"内部服务器错误: {str(exc)}", "type": type(exc).__name__},
        headers=cors_headers
    )

# 注册路由
app.include_router(auth.router)
app.include_router(chat.router)

# 注册WebSocket路由
@app.websocket("/ws/{user_id}")
async def websocket_route(websocket: WebSocket, user_id: int, token: str = Query(...)):
    """
    WebSocket端点
    
    - **user_id**: 用户ID（从URL路径获取）
    - **token**: JWT Token（从查询参数获取）
    """
    await websocket_endpoint(websocket, user_id, token)


@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "聊天室应用 API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )

