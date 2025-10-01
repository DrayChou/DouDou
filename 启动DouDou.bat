@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: =====================================================
:: DouDou 智能启动脚本
:: 自动检测环境、创建虚拟环境、安装依赖
:: =====================================================

echo.
echo ╔═══════════════════════════════════════════════════╗
echo ║          DouDou - 智能语音助手启动器              ║
echo ╚═══════════════════════════════════════════════════╝
echo.

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: =====================================================
:: 步骤1: 检查Python环境
:: =====================================================
echo [1/5] 检查Python环境...

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python！
    echo.
    echo 请先安装Python 3.9或更高版本：
    echo https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

:: 检查Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ 找到Python %PYTHON_VERSION%

:: 验证Python版本 >= 3.9
python -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ❌ Python版本过低，需要3.9或更高版本
    echo    当前版本: %PYTHON_VERSION%
    pause
    exit /b 1
)

:: =====================================================
:: 步骤2: 检查/创建虚拟环境
:: =====================================================
echo [2/5] 检查虚拟环境...

if not exist ".venv\" (
    echo 🆕 创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败！
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
    set NEED_INSTALL=1
) else (
    echo ✅ 虚拟环境已存在
)

:: =====================================================
:: 步骤3: 激活虚拟环境
:: =====================================================
echo [3/5] 激活虚拟环境...

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
) else (
    echo ❌ 虚拟环境损坏，正在重建...
    rmdir /s /q .venv
    python -m venv .venv
    call .venv\Scripts\activate.bat
    set NEED_INSTALL=1
)

:: =====================================================
:: 步骤4: 检查/安装依赖
:: =====================================================
echo [4/5] 检查依赖...

:: 检查关键依赖是否已安装
python -c "import flet" >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1

if defined NEED_INSTALL (
    echo 📦 正在安装依赖包...
    echo    这可能需要几分钟时间，请耐心等待...
    echo.

    :: 升级pip
    python -m pip install --upgrade pip --quiet

    :: 安装依赖
    echo    安装中... (1/3) 基础依赖
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo ❌ 依赖安装失败！
        echo.
        echo 请检查网络连接，或手动运行：
        echo   .venv\Scripts\activate.bat
        echo   pip install -r requirements.txt
        pause
        exit /b 1
    )

    echo    安装中... (2/3) 音频处理库
    echo    安装中... (3/3) AI模型库 (这一步可能较慢)
    echo.
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖已就绪
)

:: =====================================================
:: 步骤5: 启动应用
:: =====================================================
echo [5/5] 启动应用...
echo.
echo ╔═══════════════════════════════════════════════════╗
echo ║              DouDou 正在启动...                   ║
echo ╚═══════════════════════════════════════════════════╝
echo.

:: 启动应用
python main.py

:: 应用退出后的处理
if errorlevel 1 (
    echo.
    echo ═══════════════════════════════════════════════════
    echo ❌ 应用运行出错
    echo ═══════════════════════════════════════════════════
    echo.
    echo 常见问题解决：
    echo   1. 音频设备问题 - 请以管理员权限运行 run_as_admin.bat
    echo   2. 依赖问题 - 删除 .venv 文件夹后重新运行本脚本
    echo   3. FunASR模型问题 - 首次运行会自动下载模型，需要网络连接
    echo.
) else (
    echo.
    echo ✅ DouDou 已正常退出
)

echo.
pause
