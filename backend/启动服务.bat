@echo off
chcp 65001 >nul
title 实时聊天平台 - 后端服务

echo.
echo ============================================
echo   实时聊天平台 - 后端服务启动
echo ============================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"
echo 当前目录: %CD%
echo.

REM 检查Python
echo [1/5] 检查Python环境...

REM 尝试多种方式查找Python
set PYTHON_CMD=
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    python --version
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
        py --version
    ) else (
        REM 尝试使用完整路径
        if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
            set PYTHON_CMD=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe
            "%PYTHON_CMD%" --version
        ) else (
            echo [错误] 未找到Python，请先安装Python 3.9+
            echo.
            echo 提示: 如果已安装Python但无法找到，请尝试：
            echo   1. 使用 py 命令（Python启动器）
            echo   2. 将Python添加到系统PATH环境变量
            pause
            exit /b 1
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo [错误] 无法确定Python命令
    pause
    exit /b 1
)

echo [OK] Python已找到: %PYTHON_CMD%
echo.

REM 创建虚拟环境
echo [2/5] 检查虚拟环境...
if not exist "venv\Scripts\python.exe" (
    echo 虚拟环境不存在，正在创建...
    "%PYTHON_CMD%" -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [OK] 虚拟环境创建成功
) else (
    echo [OK] 虚拟环境已存在
)
echo.

REM 激活虚拟环境
echo [3/5] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)
echo [OK] 虚拟环境已激活
echo.

REM 安装依赖
echo [4/5] 检查依赖...
if not exist "venv\Scripts\uvicorn.exe" (
    echo 正在安装依赖包，这可能需要几分钟...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 安装依赖失败
        pause
        exit /b 1
    )
    echo [OK] 依赖安装成功
) else (
    echo [OK] 依赖已安装
)
echo.

REM 创建.env文件
if not exist ".env" (
    if exist "env.example" (
        echo 创建.env文件...
        copy env.example .env >nul
        echo [提示] 已创建.env文件，请编辑其中的SECRET_KEY
    )
)

REM 启动服务
echo [5/5] 启动服务...
echo.
echo ============================================
echo   服务信息
echo ============================================
echo   服务地址: http://localhost:8000
echo   API文档:  http://localhost:8000/docs
echo   ReDoc:    http://localhost:8000/redoc
echo ============================================
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 使用虚拟环境中的Python运行uvicorn
venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo [错误] 服务启动失败
    echo 请检查错误信息
    pause
)

