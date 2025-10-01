#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DouDou - 智能语音助手
应用入口文件
"""

import sys
import os

print("正在导入模块...")
try:
    import flet as ft
    print("✅ flet 导入成功")
except ImportError as e:
    print(f"❌ flet 导入失败: {e}")
    print("当前 Python 路径:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    input("按回车键退出...")
    sys.exit(1)

# 尝试导入 flet_app 模块
print("正在导入 flet_app 模块...")

# 获取当前脚本的目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe环境
    base_path = os.path.dirname(sys.executable)
    print(f"打包环境，基础路径: {base_path}")
else:
    # 如果是开发环境
    base_path = os.path.dirname(os.path.abspath(__file__))
    print(f"开发环境，基础路径: {base_path}")

# 在打包环境中，src目录的内容会被复制到根目录
# 在开发环境中，src目录在项目根目录下
import_successful = False

# 首先尝试直接从src导入（开发环境）
try:
    from src.flet_app import QuQuFletApp
    print("✅ src.flet_app 导入成功")
    import_successful = True
except ImportError:
    print("⚠️  src.flet_app 导入失败")

# 如果失败，尝试从根目录导入（打包环境）
if not import_successful:
    try:
        # 在打包环境中，src内容被复制到根目录，但src目录本身也存在
        # 所以需要确保src目录在路径中
        src_path = os.path.join(base_path, 'src')
        if os.path.exists(src_path) and src_path not in sys.path:
            sys.path.insert(0, src_path)

        from flet_app import QuQuFletApp
        print("✅ flet_app 导入成功")
        import_successful = True
    except ImportError:
        print("❌ 根目录导入失败")

# 如果所有尝试都失败，显示调试信息
if not import_successful:
    print(f"❌ 错误：无法找到 flet_app 模块")
    print(f"\n当前工作目录: {os.getcwd()}")
    print("当前 Python 路径:")
    for i, path in enumerate(sys.path[:5]):
        print(f"  {i}: {path}")

    # 检查可能的路径
    possible_paths = [
        os.path.join(base_path, 'src'),
        base_path,
    ]

    print("\n检查的路径:")
    for i, path in enumerate(possible_paths):
        exists = os.path.exists(path)
        print(f"  {i+1}. {path} - {'存在' if exists else '不存在'}")
        if exists:
            try:
                flet_app_path = os.path.join(path, 'flet_app.py')
                if os.path.exists(flet_app_path):
                    print(f"    ✅ 找到 flet_app.py")
                else:
                    print(f"    ❌ 未找到 flet_app.py")
                print(f"    目录内容: {os.listdir(path)[:5]}...")
            except:
                print(f"    无法列出目录内容")

    # 在非打包环境中暂停，打包环境中直接退出
    if not getattr(sys, 'frozen', False):
        input("按回车键退出...")
    sys.exit(1)


def main():
    """应用主入口"""
    print("DouDou - 智能语音助手启动中...")
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"脚本路径: {__file__}")
    print(f"sys.path: {sys.path[:3]}...")  # 只显示前3个路径
    try:
        print("正在启动 Flet 应用...")
        # 启动 Flet 应用
        ft.app(
            target=QuQuFletApp,
            assets_dir="assets"
        )
    except Exception as e:
        print(f"[ERROR] 应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()