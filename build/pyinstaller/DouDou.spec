# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
SRC_DIR = ROOT_DIR / "src"

block_cipher = None

a = Analysis(
    [str(ROOT_DIR / "main.py")],
    pathex=[str(ROOT_DIR), str(SRC_DIR)],
    binaries=[],
    datas=[
        # 包含src目录
        (str(SRC_DIR), "src"),
        # 包含配置文件
        (str(ROOT_DIR / "doudou_settings.json" if os.path.exists(ROOT_DIR / "doudou_settings.json") else ROOT_DIR / "ququ_settings.json"), "."),
        # 包含assets目录（如果存在）
        (str(ROOT_DIR / "assets"), "assets") if os.path.exists(ROOT_DIR / "assets") else None,
        # 包含启动脚本
        (str(ROOT_DIR / "run.bat"), ".") if os.path.exists(ROOT_DIR / "run.bat") else None,
        (str(ROOT_DIR / "run_as_admin.bat"), ".") if os.path.exists(ROOT_DIR / "run_as_admin.bat") else None,
    ],
    hiddenimports=[
        # Flet相关
        "flet",
        "flet.app",
        "flet.core",
        "flet.runtime",
        "flet.utils",
        # 音频处理
        "pyaudio",
        "sounddevice",
        "numpy",
        "scipy",
        "scipy.io",
        "scipy.io.wavfile",
        "librosa",
        # FunASR相关
        "funasr",
        "funasr.auto",
        "funasr.tasks",
        "funasr.utils",
        "modelscope",
        "torch",
        "torchaudio",
        "omegaconf",
        "hydra",
        "torch_complex",
        # 系统相关
        "threading",
        "multiprocessing",
        "concurrent.futures",
        # 其他
        "requests",
        "yaml",
        "json",
        "datetime",
        "tempfile",
        "wave",
        "audioop",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        "matplotlib",
        "PIL",
        "cv2",
        "pandas",
        "jupyter",
        "IPython",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 过滤掉None值
a.datas = [item for item in a.datas if item is not None]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DouDou',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windows下不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT_DIR / "assets" / "icon.ico") if os.path.exists(ROOT_DIR / "assets" / "icon.ico") else None,
)

# macOS专用配置
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name='DouDou.app',
        icon=str(ROOT_DIR / "assets" / "icon.icns") if os.path.exists(ROOT_DIR / "assets" / "icon.icns") else None,
        bundle_identifier='com.doudou.app',
        info_plist={
            'CFBundleName': 'DouDou',
            'CFBundleDisplayName': 'DouDou',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleIdentifier': 'com.doudou.app',
            'NSHighResolutionCapable': True,
            'LSApplicationCategoryType': 'public.app-category.utilities',
        },
    )