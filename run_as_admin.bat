@echo off
REM 蛐蛐 Flet 应用 - 管理员权限启动器
echo 蛐蛐语音助手 - 管理员权限启动
echo ====================================

REM 检查是否已经是管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ 已获得管理员权限
    goto :run_app
) else (
    echo ⚠️ 需要管理员权限，正在请求提升...
    goto :request_admin
)

:request_admin
REM 请求管理员权限并重新运行
powershell -Command "Start-Process '%~f0' -Verb RunAs"
exit /b

:run_app
REM 切换到脚本所在目录
cd /d "%~dp0"

echo 📍 当前目录: %CD%

REM 检查 Python 和虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo 🔧 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️ 未找到虚拟环境，使用系统 Python
)

REM 检查依赖
python -c "import flet, pyaudio, numpy" >nul 2>&1
if errorlevel 1 (
    echo ❌ 依赖缺失，正在安装...
    pip install -r requirements.txt
)

echo 🚀 启动蛐蛐语音助手（管理员模式）...
echo.
echo 💡 管理员权限可以解决音频驱动兼容性问题
echo 💡 如果仍有问题，请检查麦克风权限设置
echo.

python main.py

echo.
echo 📱 应用已退出
pause