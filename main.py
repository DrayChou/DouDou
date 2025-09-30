#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蛐蛐 (QuQu) - 智能语音助手
应用入口文件
"""

import sys
import os

# 添加 src 目录到 Python 路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

import flet as ft
from flet_app import QuQuFletApp


def main():
    """应用主入口"""
    try:
        # 启动 Flet 应用
        ft.app(
            target=QuQuFletApp,
            assets_dir="assets"
        )
    except Exception as e:
        print(f"[ERROR] 应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()