@echo off
chcp 65001
echo ============================================================
echo DouDou - PyTorch CUDA 版本安装脚本
echo ============================================================
echo.
echo 当前虚拟环境PyTorch版本为旧版本，需要升级到CUDA版本
echo 您的GPU: NVIDIA RTX 3070
echo CUDA驱动版本: 12.6
echo.
echo 即将执行以下操作：
echo 1. 卸载虚拟环境中的旧版PyTorch
echo 2. 安装PyTorch 2.8.0 + CUDA 12.6 版本到虚拟环境
echo 3. 验证安装结果
echo.
echo 注意：下载大小约 2.9GB，请确保网络连接稳定
echo.
pause

echo.
echo [1/3] 卸载虚拟环境中的旧版PyTorch...
.venv\Scripts\pip.exe uninstall -y torch torchvision torchaudio

echo.
echo [2/3] 安装PyTorch 2.8.0 + CUDA 12.6到虚拟环境...
echo 提示：下载约2.9GB，请耐心等待...
.venv\Scripts\pip.exe install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

echo.
echo [3/3] 验证安装结果...
echo ============================================================
.venv\Scripts\python.exe -c "import torch; print('PyTorch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available()); print('CUDA编译版本:', torch.version.cuda if hasattr(torch.version, 'cuda') and torch.version.cuda else 'N/A'); print('GPU设备:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
echo ============================================================

echo.
echo 安装完成！请重新运行 DouDou 应用查看效果
echo 预期显示：计算设备: 🚀 GPU (CUDA)
echo.
pause
