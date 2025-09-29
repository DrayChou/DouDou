@echo off
echo 蛐蛐 Flet 应用启动器 (标准 Python 虚拟环境)
echo ================================================
echo.

REM 切换到项目根目录
cd /d "%~dp0.."

REM 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未找到，请确保 Python 已安装并添加到 PATH
    pause
    exit /b 1
)

echo ✅ Python 可用

REM 检查虚拟环境是否存在
if not exist ".venv" (
    echo 📦 创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
)

echo 🔧 激活虚拟环境...
call .venv\Scripts\activate.bat

REM 升级 pip
echo 📦 升级 pip...
python -m pip install --upgrade pip --quiet

REM 检查依赖是否安装
echo 📦 检查依赖...
python -c "import flet, pyaudio, numpy" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 依赖缺失，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo ✅ 所有依赖已安装

REM 检查 FunASR 模型
if not exist "%USERPROFILE%\.cache\modelscope" (
    echo 📥 首次运行，下载 FunASR 模型...
    python download_models.py
)

echo 🚀 启动应用...
echo.
echo 💡 提示：应用启动后会打开GUI窗口
echo 💡 关闭窗口或按 Ctrl+C 退出应用
echo.

python flet_app.py

echo.
echo 🎉 应用已退出
pause