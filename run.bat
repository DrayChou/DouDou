@echo off
chcp 65001 >nul
echo ========================================
echo   DouDou - 智能语音助手
echo ========================================
echo.

REM 检查虚拟环境是否存在
if exist ".venv\Scripts\python.exe" (
    echo [INFO] 使用现有虚拟环境启动应用...

    REM 检查关键依赖是否已安装
    .venv\Scripts\python.exe -c "import flet, numpy" 2>nul
    if errorlevel 1 (
        echo [WARN] 依赖不完整，正在安装...
        .venv\Scripts\python.exe -m pip install --upgrade pip
        .venv\Scripts\python.exe -m pip install -r requirements.txt
    ) else (
        echo [INFO] 所有依赖已安装
    )
) else (
    echo [WARN] 虚拟环境不存在，正在创建...

    REM 创建虚拟环境
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] 虚拟环境创建失败
        echo [提示] 请确保已安装 Python 3.9+
        pause
        exit /b 1
    )

    echo [INFO] 安装依赖包...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo.
echo [INFO] 启动 Flet 应用...
echo [提示] 应用启动后会打开 GUI 窗口
echo.

.venv\Scripts\python.exe main.py

echo.
echo [INFO] 应用运行完成
pause