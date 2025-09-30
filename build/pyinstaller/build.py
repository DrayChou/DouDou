#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DouDou 应用打包脚本
支持 Windows 平台打包
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def check_dependencies():
    """检查构建依赖"""
    print("🔍 检查构建依赖...")

    try:
        import PyInstaller
        print(f"✅ PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("请运行: pip install -r build/pyinstaller/build_requirements.txt")
        return False

    return True

def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")

    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  🗑️  删除 {dir_name}")

    # 清理spec文件
    for spec_file in Path(".").glob("*.spec"):
        if spec_file.name != "DouDou.spec":
            spec_file.unlink()
            print(f"  🗑️  删除 {spec_file}")

def build_executable():
    """构建可执行文件"""
    print("🏗️  开始构建可执行文件...")

    # 根据平台选择构建选项
    current_platform = platform.system().lower()

    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "build/pyinstaller/DouDou.spec"
    ]

    if current_platform == "windows":
        cmd.extend([
            "--windowed",  # Windows下不显示控制台
            "--noupx",     # UPX可能导致一些问题，暂时禁用
        ])
        print("🪟 检测到Windows平台，使用窗口化模式")
    elif current_platform == "darwin":  # macOS
        cmd.extend(["--windowed"])
        print("🍎 检测到macOS平台，创建应用包")
    else:  # Linux
        print("🐧 检测到Linux平台")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def create_distribution():
    """创建发布包"""
    print("📦 创建发布包...")

    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ dist目录不存在")
        return False

    current_platform = platform.system().lower()
    version = "1.0.0"

    if current_platform == "windows":
        exe_name = "DouDou.exe"
        zip_name = f"DouDou-Windows-x64-v{version}.zip"
    elif current_platform == "darwin":
        app_name = "DouDou.app"
        zip_name = f"DouDou-macOS-x64-v{version}.zip"
    else:
        exe_name = "DouDou"
        zip_name = f"DouDou-Linux-x64-v{version}.tar.gz"

    # 创建发布目录
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)

    # 复制必要文件
    files_to_copy = [
        "README.md",
        "LICENSE",
        "doudou_settings.json",
        "run.bat" if current_platform == "windows" else None,
        "run_as_admin.bat" if current_platform == "windows" else None,
    ]

    for file_name in files_to_copy:
        if file_name and os.path.exists(file_name):
            shutil.copy2(file_name, release_dir / file_name)
            print(f"📄 复制 {file_name}")

    # 复制可执行文件
    if current_platform == "windows":
        exe_path = dist_dir / exe_name
        if exe_path.exists():
            shutil.copy2(exe_path, release_dir / exe_name)
            print(f"📄 复制 {exe_name}")
    elif current_platform == "darwin":
        app_path = dist_dir / "DouDou.app"
        if app_path.exists():
            shutil.copytree(app_path, release_dir / "DouDou.app", dirs_exist_ok=True)
            print(f"📁 复制 DouDou.app")
    else:
        exe_path = dist_dir / exe_name
        if exe_path.exists():
            shutil.copy2(exe_path, release_dir / exe_name)
            print(f"📄 复制 {exe_name}")

    # 创建压缩包
    import zipfile
    if current_platform == "windows":
        with zipfile.ZipFile(release_dir / zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in release_dir.rglob("*"):
                if file_path.is_file() and file_path.name != zip_name:
                    arcname = file_path.relative_to(release_dir)
                    zipf.write(file_path, arcname)
    else:
        import tarfile
        with tarfile.open(release_dir / zip_name, 'w:gz') as tar:
            tar.add(release_dir, arcname=os.path.basename(release_dir))

    print(f"📦 发布包已创建: {release_dir / zip_name}")
    return True

def main():
    """主函数"""
    print("🚀 DouDou 应用打包工具")
    print("=" * 50)

    # 检查平台支持
    current_platform = platform.system().lower()
    print(f"🖥️  当前平台: {platform.system()} {platform.machine()}")

    if current_platform == "windows":
        print("✅ Windows平台支持: 完整支持")
    elif current_platform == "darwin":
        print("✅ macOS平台支持: 完整支持 (未测试)")
    else:
        print("✅ Linux平台支持: 基础支持 (未测试)")
        print("⚠️  注意: Linux平台需要额外的音频库依赖")

    print()

    # 执行构建步骤
    if not check_dependencies():
        sys.exit(1)

    clean_build()

    if not build_executable():
        sys.exit(1)

    if not create_distribution():
        sys.exit(1)

    print()
    print("🎉 打包完成！")
    print("📁 发布文件位置: ./release/")
    print("🚀 可以分发给用户使用了！")

    # 显示文件大小
    release_dir = Path("release")
    if release_dir.exists():
        total_size = sum(f.stat().st_size for f in release_dir.rglob("*") if f.is_file())
        print(f"📊 发布包总大小: {total_size / (1024*1024):.1f} MB")

if __name__ == "__main__":
    main()