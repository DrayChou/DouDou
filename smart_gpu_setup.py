#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DouDou 智能GPU配置检测和安装脚本

根据用户硬件自动检测并推荐最佳PyTorch配置
"""

import subprocess
import sys
import os
import re
from pathlib import Path

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"{text}")
    print(f"{'='*60}\n")

def print_success(text):
    """打印成功信息"""
    print(f"✅ {text}")

def print_error(text):
    """打印错误信息"""
    print(f"❌ {text}")

def print_warning(text):
    """打印警告信息"""
    print(f"⚠️  {text}")

def print_info(text):
    """打印信息"""
    print(f"ℹ️  {text}")

def get_nvidia_info():
    """
    检测NVIDIA GPU信息

    Returns:
        dict: GPU信息 {'name': str, 'driver': str, 'cuda': str} 或 None
    """
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            check=True
        )

        gpu_info = result.stdout.strip().split(',')

        # 获取CUDA版本
        cuda_result = subprocess.run(
            ['nvidia-smi'],
            capture_output=True,
            text=True,
            check=True
        )

        # 从nvidia-smi输出中提取CUDA版本
        cuda_match = re.search(r'CUDA Version:\s*(\d+\.\d+)', cuda_result.stdout)
        cuda_version = cuda_match.group(1) if cuda_match else '12.6'

        return {
            'name': gpu_info[0].strip(),
            'driver': gpu_info[1].strip(),
            'memory': gpu_info[2].strip(),
            'cuda': cuda_version
        }
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"DEBUG: nvidia-smi 调用失败: {e}")
        return None
    except Exception as e:
        print(f"DEBUG: 解析GPU信息失败: {e}")
        return None

def get_pytorch_index_from_cuda(cuda_version):
    """
    根据CUDA版本确定PyTorch索引

    Args:
        cuda_version: CUDA版本字符串 (如 "12.6")

    Returns:
        str: PyTorch索引 (如 "cu126")
    """
    version_map = {
        '11.8': 'cu118',
        '12.1': 'cu121',
        '12.4': 'cu124',
        '12.6': 'cu126',
        '12.8': 'cu128',
    }

    # 提取主版本号
    major_minor = '.'.join(cuda_version.split('.')[:2])

    # 如果精确匹配
    if major_minor in version_map:
        return version_map[major_minor]

    # 否则选择最接近的版本（向下兼容）
    if cuda_version.startswith('12.'):
        return 'cu126'  # 默认使用12.6
    elif cuda_version.startswith('11.'):
        return 'cu118'
    else:
        return 'cu126'  # 默认

def get_current_pytorch_info():
    """
    检测当前虚拟环境中的PyTorch信息

    Returns:
        dict: PyTorch信息或None
    """
    venv_python = Path('.venv/Scripts/python.exe')
    if not venv_python.exists():
        return None

    try:
        # 检查是否安装PyTorch
        result = subprocess.run(
            [str(venv_python), '-c', 'import torch'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {'installed': False}

        # 获取版本信息
        version_cmd = [
            str(venv_python), '-c',
            'import torch; '
            'print(torch.__version__); '
            'print(torch.cuda.is_available()); '
            'print(torch.version.cuda if hasattr(torch.version, "cuda") and torch.version.cuda else ""); '
            'print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")'
        ]

        result = subprocess.run(version_cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')

        return {
            'installed': True,
            'version': lines[0],
            'cuda_available': lines[1] == 'True',
            'cuda_version': lines[2] if len(lines) > 2 else '',
            'gpu_name': lines[3] if len(lines) > 3 else ''
        }
    except Exception as e:
        return {'installed': False, 'error': str(e)}

def recommend_action(gpu_info, pytorch_info, recommended_index):
    """
    根据检测结果推荐操作

    Returns:
        str: 'none' | 'install' | 'upgrade'
    """
    if not pytorch_info or not pytorch_info.get('installed'):
        return 'install'

    if not pytorch_info.get('cuda_available'):
        return 'upgrade'  # CPU版本需要升级

    # 检查CUDA版本是否匹配
    current_cuda = pytorch_info.get('cuda_version', '')
    if current_cuda:
        # 提取主版本号进行比较
        current_major = current_cuda.split('.')[0] if '.' in current_cuda else current_cuda
        recommended_major = recommended_index[2:]  # cu126 -> 126

        if current_major == recommended_major or current_cuda.replace('.', '')[:3] == recommended_major:
            return 'none'  # 版本匹配

    return 'upgrade'  # 版本不匹配，建议升级

def install_pytorch(pytorch_index, is_upgrade=False):
    """
    安装或升级PyTorch

    Args:
        pytorch_index: PyTorch CUDA索引 (如 "cu126")
        is_upgrade: 是否是升级操作
    """
    venv_pip = Path('.venv/Scripts/pip.exe')

    if is_upgrade:
        print_info("卸载旧版本...")
        subprocess.run(
            [str(venv_pip), 'uninstall', '-y', 'torch', 'torchvision', 'torchaudio'],
            check=False
        )

    print_info(f"安装 PyTorch 2.8.0 + CUDA {pytorch_index}...")
    print_warning("下载约2.9GB，请耐心等待...")

    result = subprocess.run(
        [
            str(venv_pip), 'install',
            'torch', 'torchvision', 'torchaudio',
            '--index-url', f'https://download.pytorch.org/whl/{pytorch_index}'
        ],
        check=False
    )

    return result.returncode == 0

def verify_installation():
    """验证安装结果"""
    venv_python = Path('.venv/Scripts/python.exe')

    print_header("验证安装")

    result = subprocess.run(
        [
            str(venv_python), '-c',
            'import torch; '
            'print("PyTorch版本:", torch.__version__); '
            'print("CUDA可用:", torch.cuda.is_available()); '
            'print("CUDA版本:", torch.version.cuda if hasattr(torch.version, "cuda") and torch.version.cuda else "N/A"); '
            'print("GPU设备:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A")'
        ],
        check=False
    )

    return result.returncode == 0

def main():
    """主函数"""
    print_header("DouDou - 智能GPU配置检测")

    # 步骤1: 检测GPU
    print("[1/5] 检测GPU硬件...")
    gpu_info = get_nvidia_info()

    if not gpu_info:
        print_error("未检测到NVIDIA GPU或驱动未安装")
        print_info("建议：使用CPU模式，无需操作")
        return

    print_success(f"检测到GPU: {gpu_info['name']}")
    print(f"    驱动版本: {gpu_info['driver']}")
    print(f"    显存: {gpu_info['memory']}")

    # 步骤2: 检测CUDA版本
    print(f"\n[2/5] 检测CUDA版本...")
    print_success(f"CUDA版本: {gpu_info['cuda']}")

    recommended_index = get_pytorch_index_from_cuda(gpu_info['cuda'])
    print(f"    推荐PyTorch索引: {recommended_index}")

    # 步骤3: 检测虚拟环境
    print(f"\n[3/5] 检测虚拟环境中的PyTorch...")
    if not Path('.venv/Scripts/python.exe').exists():
        print_error("虚拟环境不存在")
        print_info("请先创建虚拟环境: python -m venv .venv")
        return

    pytorch_info = get_current_pytorch_info()

    if not pytorch_info or not pytorch_info.get('installed'):
        print_error("PyTorch未安装")
    elif not pytorch_info.get('cuda_available'):
        print_error(f"当前PyTorch版本: {pytorch_info.get('version')} (无CUDA支持)")
    else:
        print_success(f"当前PyTorch版本: {pytorch_info.get('version')}")
        print(f"    CUDA支持: {pytorch_info.get('cuda_version')}")
        print(f"    检测到的GPU: {pytorch_info.get('gpu_name')}")

    # 步骤4: 推荐操作
    print(f"\n[4/5] 配置建议...")
    action = recommend_action(gpu_info, pytorch_info, recommended_index)

    if action == 'none':
        print_success("当前配置已是最佳状态，无需操作")
        return
    elif action == 'install':
        print_error("需要安装PyTorch CUDA版本")
        print(f"\n即将安装:")
        print(f"  - PyTorch 2.8.0 + CUDA {recommended_index}")
        print(f"  - 下载大小: 约2.9GB")
    else:  # upgrade
        print_warning("建议升级PyTorch以匹配CUDA版本")
        print(f"\n当前版本: {pytorch_info.get('version')} (CUDA {pytorch_info.get('cuda_version', 'N/A')})")
        print(f"建议版本: 2.8.0 (CUDA {recommended_index})")

    # 确认
    confirm = input(f"\n确认{'安装' if action == 'install' else '升级'}? (Y/N): ")
    if confirm.upper() != 'Y':
        print_info("操作已取消")
        return

    # 步骤5: 执行安装
    print(f"\n[5/5] {'安装' if action == 'install' else '升级'}PyTorch...")
    success = install_pytorch(recommended_index, is_upgrade=(action == 'upgrade'))

    if success:
        verify_installation()
        print_success("安装完成！请重新运行 DouDou")
        print_info("预期显示: 计算设备: 🚀 GPU (CUDA)")
    else:
        print_error("安装失败，请检查网络连接或手动安装")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print_error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
