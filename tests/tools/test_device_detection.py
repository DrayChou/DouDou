#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备检测测试脚本

测试自动GPU检测功能
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.direct_funasr import DirectFunASR

def test_device_detection():
    """测试设备检测功能"""
    print("=" * 60)
    print("FunASR 设备自动检测测试")
    print("=" * 60)

    # 创建DirectFunASR实例（会自动检测设备）
    funasr = DirectFunASR()

    print(f"\n✅ 检测到设备: {funasr.device}")

    # 显示详细的PyTorch信息
    try:
        import torch
        print("\n" + "=" * 60)
        print("PyTorch 环境信息")
        print("=" * 60)
        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"CUDA版本: {torch.version.cuda}")
            print(f"GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
                props = torch.cuda.get_device_properties(i)
                print(f"    显存: {props.total_memory / (1024**3):.2f} GB")
                print(f"    计算能力: {props.major}.{props.minor}")

        if hasattr(torch.backends, 'mps'):
            print(f"MPS可用: {torch.backends.mps.is_available()}")

        if hasattr(torch, 'xpu'):
            print(f"XPU可用: {torch.xpu.is_available()}")

    except ImportError:
        print("\n⚠️  PyTorch未安装，无法显示详细信息")

    # 检查FunASR状态
    print("\n" + "=" * 60)
    print("FunASR 状态")
    print("=" * 60)
    status = funasr.check_status()
    print(f"已安装: {status.get('installed', False)}")
    print(f"已初始化: {status.get('initialized', False)}")
    print(f"设备: {status.get('device', 'unknown')}")
    if 'version' in status:
        print(f"版本: {status['version']}")

    print("\n" + "=" * 60)
    print("设备检测测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_device_detection()
