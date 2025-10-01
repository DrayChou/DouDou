@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo DouDou - 智能GPU配置检测脚本
echo ============================================================
echo.

REM 步骤1: 检测NVIDIA GPU
echo [1/5] 检测GPU硬件...
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到NVIDIA GPU或驱动未安装
    echo    建议：使用CPU模式，无需操作
    goto :END
)

for /f "tokens=*" %%i in ('nvidia-smi --query-gpu=name --format=csv,noheader') do set GPU_NAME=%%i
for /f "tokens=*" %%i in ('nvidia-smi --query-gpu=driver_version --format=csv,noheader') do set DRIVER_VERSION=%%i
echo ✅ 检测到GPU: !GPU_NAME!
echo    驱动版本: !DRIVER_VERSION!

REM 步骤2: 检测CUDA版本
echo.
echo [2/5] 检测CUDA版本...
for /f "tokens=*" %%i in ('nvidia-smi --query-gpu=cuda_version --format=csv,noheader') do set CUDA_VERSION=%%i
echo ✅ CUDA版本: !CUDA_VERSION!

REM 确定需要的PyTorch版本
set PYTORCH_INDEX=cu126
if "!CUDA_VERSION:~0,4!"=="11.8" set PYTORCH_INDEX=cu118
if "!CUDA_VERSION:~0,4!"=="12.1" set PYTORCH_INDEX=cu121
if "!CUDA_VERSION:~0,4!"=="12.4" set PYTORCH_INDEX=cu124
echo    推荐PyTorch索引: !PYTORCH_INDEX!

REM 步骤3: 检测虚拟环境中的PyTorch
echo.
echo [3/5] 检测虚拟环境中的PyTorch...
if not exist ".venv\Scripts\python.exe" (
    echo ❌ 虚拟环境不存在
    echo    请先创建虚拟环境: python -m venv .venv
    goto :END
)

.venv\Scripts\python.exe -c "import torch" >nul 2>&1
if errorlevel 1 (
    echo ❌ PyTorch未安装
    set NEED_INSTALL=1
    goto :DECIDE
)

REM 获取当前PyTorch版本和CUDA支持
for /f "tokens=*" %%i in ('.venv\Scripts\python.exe -c "import torch; print(torch.__version__)"') do set CURRENT_TORCH=%%i
.venv\Scripts\python.exe -c "import torch; exit(0 if torch.cuda.is_available() else 1)" >nul 2>&1
if errorlevel 1 (
    echo ❌ 当前PyTorch版本: !CURRENT_TORCH! (无CUDA支持)
    set NEED_INSTALL=1
) else (
    for /f "tokens=*" %%i in ('.venv\Scripts\python.exe -c "import torch; print(torch.version.cuda if torch.version.cuda else '')"') do set CURRENT_CUDA=%%i
    for /f "tokens=*" %%i in ('.venv\Scripts\python.exe -c "import torch; print(torch.cuda.get_device_name(0))"') do set CURRENT_GPU=%%i
    echo ✅ 当前PyTorch版本: !CURRENT_TORCH!
    echo    CUDA支持: !CURRENT_CUDA!
    echo    检测到的GPU: !CURRENT_GPU!

    REM 检查CUDA版本是否匹配
    if "!CURRENT_CUDA:~0,4!"=="!CUDA_VERSION:~0,4!" (
        echo ✅ PyTorch CUDA版本与驱动匹配，无需操作
        set NEED_INSTALL=0
    ) else (
        echo ⚠️  PyTorch CUDA版本(!CURRENT_CUDA!)与驱动(!CUDA_VERSION!)不完全匹配
        echo    建议升级以获得最佳性能
        set NEED_INSTALL=2
    )
)

:DECIDE
echo.
echo [4/5] 配置建议...
if "!NEED_INSTALL!"=="0" (
    echo ✅ 当前配置已是最佳状态，无需操作
    goto :END
)

if "!NEED_INSTALL!"=="1" (
    echo ❌ 需要安装PyTorch CUDA版本
    echo.
    echo 即将安装：
    echo - PyTorch 2.8.0 + CUDA !PYTORCH_INDEX!
    echo - 下载大小: 约2.9GB
    echo.
    set /p CONFIRM="确认安装? (Y/N): "
    if /i "!CONFIRM!" neq "Y" goto :END
    goto :INSTALL
)

if "!NEED_INSTALL!"=="2" (
    echo ⚠️  建议升级PyTorch以匹配CUDA版本
    echo.
    echo 当前版本: !CURRENT_TORCH! (CUDA !CURRENT_CUDA!)
    echo 建议版本: 2.8.0 (CUDA !PYTORCH_INDEX!)
    echo.
    set /p CONFIRM="确认升级? (Y/N): "
    if /i "!CONFIRM!" neq "Y" goto :END
    goto :INSTALL
)

:INSTALL
echo.
echo [5/5] 安装PyTorch...
if "!NEED_INSTALL!"=="2" (
    echo 卸载旧版本...
    .venv\Scripts\pip.exe uninstall -y torch torchvision torchaudio
)

echo 安装 PyTorch 2.8.0 + CUDA !PYTORCH_INDEX!...
echo 提示: 下载约2.9GB，请耐心等待...
.venv\Scripts\pip.exe install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/!PYTORCH_INDEX!

echo.
echo ============================================================
echo 验证安装...
echo ============================================================
.venv\Scripts\python.exe -c "import torch; print('PyTorch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available()); print('CUDA版本:', torch.version.cuda if hasattr(torch.version, 'cuda') and torch.version.cuda else 'N/A'); print('GPU设备:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
echo ============================================================
echo.
echo ✅ 安装完成！请重新运行 DouDou
goto :END

:END
echo.
echo ============================================================
pause
