# DouDou 项目文件结构

## 📁 根目录结构

```
ququ_flet/
├── 📄 main.py                    # 应用主入口文件
├── 📄 README.md                  # 项目说明文档
├── 📄 LICENSE                    # 开源协议
├── 📄 CLAUDE.md                  # Claude Code 配置文件
├── 📄 requirements.txt           # 项目依赖
├── 📄 requirements_build.txt     # 构建依赖
├── 📄 build_windows.bat          # Windows 打包启动器
├── 📄 build_windows.ps1          # PowerShell 打包脚本
├── 📄 build_windows.spec         # PyInstaller 配置文件
├── 📄 clean_build.bat            # 构建环境清理脚本
├── 📄 run.bat                    # 标准启动脚本
├── 📄 run_as_admin.bat           # 管理员权限启动脚本
├── 📁 .venv/                     # Python 虚拟环境
├── 📁 build_env/                 # 构建专用虚拟环境
├── 📁 assets/                    # 应用资源文件
├── 📁 src/                       # 源代码目录
├── 📁 docs/                      # 文档目录
├── 📁 tests/                     # 测试目录
├── 📁 scripts/                   # 脚本目录
├── 📁 tools/                     # 工具目录
├── 📁 release/                   # 发布文件目录
├── 📁 build/                     # 构建临时文件
└── 📁 dist/                      # 打包输出目录
```

## 📁 src/ 源代码结构

```
src/
├── 📄 __init__.py               # 包初始化文件
├── 📄 flet_app.py               # Flet 主应用
├── 📄 flet_app_old.py           # 旧版 Flet 应用（备用）
├── 📁 core/                     # 核心功能模块
│   ├── 📄 __init__.py
│   ├── 📄 audio_engine.py       # 音频处理引擎
│   ├── 📄 vad_system.py         # 语音活动检测
│   └── 📄 ...
├── 📁 ui/                       # 用户界面模块
│   ├── 📄 __init__.py
│   └── 📄 ...
└── 📁 utils/                    # 工具模块
    ├── 📄 __init__.py
    └── 📄 ...
```

## 📁 docs/ 文档结构

```
docs/
├── 📄 BUGFIX_LOG.md             # 问题修复日志
├── 📄 SETUP_GUIDE.md            # 设置指南
├── 📄 模块化拆分规划.md           # 模块化重构计划
├── 📄 AGENTS.md                 # AI 代理配置
├── 📄 FILE_STRUCTURE.md         # 文件结构说明（本文件）
├── 📁 analysis/                 # 分析报告
│   └── 📄 VAD_Analysis_Report.md # VAD 系统分析报告
└── 📁 config/                   # 配置文件
    └── 📄 doudou_settings.json  # 应用配置文件
```

## 📁 tests/ 测试结构

```
tests/
├── 📁 standalone/               # 独立测试脚本
│   ├── 📄 test_funasr.py        # FunASR 测试
│   ├── 📄 test_simple.py        # 简单功能测试
│   └── 📄 test_vad_functionality.py # VAD 功能测试
└── 📁 (其他测试文件)             # 单元测试、集成测试等
```

## 📁 scripts/ 脚本结构

```
scripts/
├── 📄 run_flet_simple.bat       # Flet 应用简单启动器
└── 📄 (其他辅助脚本)             # 构建脚本、部署脚本等
```

## 📁 assets/ 资源结构

```
assets/
├── 🖼️ icon.ico                  # 应用图标
├── 🖼️ (其他图片资源)            # UI 图片、图标等
└── 📄 (其他资源文件)            # 音频文件、配置文件等
```

## 🗂️ 文件分类说明

### 🔧 核心文件
- `main.py` - 应用启动入口
- `src/flet_app.py` - 主要的应用逻辑
- `requirements.txt` - 运行时依赖

### 🏗️ 构建文件
- `build_windows.bat` / `build_windows.ps1` - 打包脚本
- `build_windows.spec` - PyInstaller 配置
- `requirements_build.txt` - 构建依赖

### 📖 文档文件
- `README.md` - 项目介绍
- `docs/` 目录下的所有文档

### 🧪 测试文件
- `tests/standalone/` - 独立测试脚本
- `tests/` - 其他测试文件

### ⚙️ 配置文件
- `docs/config/doudou_settings.json` - 应用配置
- `.env` / `.env.example` - 环境变量配置

### 🎨 资源文件
- `assets/` - 应用图标、图片等资源

这个结构确保了：
- ✅ 清晰的模块分离
- ✅ 便于维护和扩展
- ✅ 符合 Python 项目最佳实践
- ✅ 支持多种部署方式