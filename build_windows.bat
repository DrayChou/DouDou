@echo off
echo 🚀 DouDou Windows 打包工具
echo ========================================

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 创建虚拟环境
echo 📦 创建构建虚拟环境...
if exist build_env rmdir /s /q build_env
python -m venv build_env
call build_env\Scripts\activate.bat

:: 安装依赖
echo 📥 安装依赖...
pip install --upgrade pip
pip install -r requirements.txt
pip install -r build\pyinstaller\build_requirements.txt

:: 运行打包脚本
echo 🏗️ 开始打包...
python build\pyinstaller\build.py

:: 清理
echo 🧹 清理虚拟环境...
deactivate
rmdir /s /q build_env

echo.
echo ✅ Windows打包完成！
echo 📁 发布文件: release\*.zip
pause