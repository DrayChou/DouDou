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

# 规范化 sys.path：确保 src 优先，其次是项目根目录
src_path = os.path.join(base_path, 'src')
if os.path.exists(src_path):
    # 去重并确保顺序: [src, base, 其他]
    rest = [p for p in sys.path if p not in (src_path, base_path)]
    sys.path = [src_path, base_path] + rest
    print(f"sys.path[0..1] 已设置为: {sys.path[:2]}")
else:
    print(f"未找到 src 目录: {src_path}")

# 首先尝试：在把 src 放入 sys.path 后，直接导入 flet_app（模块路径：src/flet_app.py）
try:
    from flet_app import QuQuFletApp
    print("✅ flet_app (from src) 导入成功")
    import_successful = True
except ImportError as e:
    print(f"⚠️  flet_app(from src) 导入失败: {e}")

# 如果失败，再尝试从根目录作为包导入 src.flet_app
if not import_successful:
    try:
        if base_path not in sys.path:
            sys.path.insert(0, base_path)
        from src.flet_app import QuQuFletApp
        print("✅ src.flet_app 导入成功")
        import_successful = True
    except ImportError as e:
        print(f"❌ src.flet_app 导入失败: {e}")

# 最后尝试：直接从文件路径加载 flet_app.py
if not import_successful:
    try:
        import importlib.util
        module_path = os.path.join(src_path, 'flet_app.py')
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location('flet_app', module_path)
            if spec and spec.loader:
                flet_app_mod = importlib.util.module_from_spec(spec)
                sys.modules['flet_app'] = flet_app_mod
                spec.loader.exec_module(flet_app_mod)
                from flet_app import QuQuFletApp
                print("✅ flet_app (from file) 导入成功")
                import_successful = True
            else:
                print("❌ 无法创建 flet_app 模块规范 (spec)")
        else:
            print(f"❌ 未找到文件: {module_path}")
    except Exception as e:
        print(f"❌ 文件路径导入失败: {e}")
        import traceback; traceback.print_exc()

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
