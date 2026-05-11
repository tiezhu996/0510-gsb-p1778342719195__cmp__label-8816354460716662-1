"""
直接启动脚本 - 无需手动激活虚拟环境
自动创建虚拟环境、安装依赖并启动服务
"""
import os
import sys
import subprocess
import platform

def run_command(cmd, check=True, cwd=None):
    """运行命令"""
    print(f"执行: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=check,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"错误输出: {result.stderr}", file=sys.stderr)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}", file=sys.stderr)
        if e.stdout:
            print(f"输出: {e.stdout}")
        if e.stderr:
            print(f"错误: {e.stderr}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"执行命令时发生错误: {e}", file=sys.stderr)
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("实时聊天平台 - 后端服务启动")
    print("=" * 50)
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print("错误: 需要Python 3.9或更高版本")
        sys.exit(1)
    
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 确定虚拟环境路径
    venv_path = "venv"
    if platform.system() == "Windows":
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        python_exe = os.path.join(venv_path, "bin", "python")
        pip_exe = os.path.join(venv_path, "bin", "pip")
    
    # 切换到backend目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    original_dir = os.getcwd()
    os.chdir(script_dir)
    
    # 检查虚拟环境是否存在
    if not os.path.exists(python_exe):
        print("\n虚拟环境不存在，正在创建...")
        venv_cmd = f'"{sys.executable}" -m venv {venv_path}'
        if not run_command(venv_cmd, cwd=script_dir):
            print("错误: 创建虚拟环境失败")
            print(f"请检查Python是否正确安装: {sys.executable}")
            sys.exit(1)
        print("虚拟环境创建成功！")
        
        # 重新检查python_exe是否存在
        if not os.path.exists(python_exe):
            print(f"错误: 虚拟环境创建后，Python可执行文件未找到: {python_exe}")
            sys.exit(1)
    
    # 检查依赖是否已安装
    uvicorn_path = os.path.join(venv_path, "Scripts", "uvicorn.exe") if platform.system() == "Windows" else os.path.join(venv_path, "bin", "uvicorn")
    if not os.path.exists(uvicorn_path):
        print("\n正在安装依赖...")
        if not os.path.exists("requirements.txt"):
            print("错误: requirements.txt文件不存在")
            sys.exit(1)
        pip_cmd = f'"{pip_exe}" install -r requirements.txt'
        if not run_command(pip_cmd, cwd=script_dir):
            print("错误: 安装依赖失败")
            print("请检查requirements.txt文件是否正确")
            sys.exit(1)
        print("依赖安装成功！")
    
    # 检查.env文件
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            print("\n.env文件不存在，从env.example创建...")
            import shutil
            shutil.copy("env.example", ".env")
            print("已创建.env文件，请编辑其中的SECRET_KEY等配置")
        else:
            print("\n警告: .env文件不存在，将使用默认配置")
    
    # 启动服务
    print("\n" + "=" * 50)
    print("启动FastAPI服务...")
    print("服务地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务")
    print("=" * 50 + "\n")
    
    # 切换到backend目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    sys.path.insert(0, script_dir)
    
    # 使用虚拟环境中的Python运行uvicorn
    print(f"\n当前工作目录: {os.getcwd()}")
    print(f"虚拟环境Python: {python_exe}")
    
    # 尝试使用虚拟环境中的uvicorn
    if platform.system() == "Windows":
        uvicorn_cmd = os.path.join(venv_path, "Scripts", "uvicorn.exe")
        python_cmd = python_exe
    else:
        uvicorn_cmd = os.path.join(venv_path, "bin", "uvicorn")
        python_cmd = python_exe
    
    # 检查uvicorn是否存在
    if not os.path.exists(uvicorn_cmd):
        print(f"错误: uvicorn未找到在 {uvicorn_cmd}")
        print("请确保依赖已正确安装")
        sys.exit(1)
    
    # 使用虚拟环境中的Python运行uvicorn
    print(f"使用: {uvicorn_cmd}")
    cmd = f'"{python_cmd}" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'
    print(f"启动命令: {cmd}\n")
    print("提示: 日志会同时输出到控制台和 backend.log 文件")
    print("=" * 50 + "\n")
    
    # 直接运行uvicorn命令
    try:
        # 切换到backend目录
        os.chdir(script_dir)
        print(f"\n正在启动服务...")
        print(f"工作目录: {os.getcwd()}")
        print(f"Python: {python_cmd}")
        print(f"命令: {python_cmd} -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000\n")
        
        # 使用subprocess.run直接运行，不捕获输出，让输出直接显示在控制台
        # 注意：不使用shell=True，直接传递参数列表
        import shlex
        result = subprocess.run(
            [python_cmd, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd=script_dir,
            check=False  # 不抛出异常，让错误信息显示
        )
        
        if result.returncode != 0:
            print(f"\n服务启动失败，退出码: {result.returncode}")
            print("请检查上面的错误信息")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n启动服务时发生错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

