<div align="center">

<!-- 在这里放置您的Logo图片 -->
<!-- 例如: <img src="assets/logo.png" width="150" /> -->
<br/>
<br/>

# DouDou

**基于 Flet 的现代化智能语音助手 | 为中文而生的下一代语音转文字工具**

</div>

<div align="center">

<!-- 徽章 (Badges) - 您可以后续替换为动态徽章服务 (如 shields.io) -->
<img src="https://img.shields.io/badge/license-Apache_2.0-blue.svg" alt="License">
<img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey" alt="Platform">
<img src="https://img.shields.io/badge/release-v1.0.0-brightgreen" alt="Release">
<img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">

</div>

<br/>

> **厌倦了复杂的语音输入工具？寻找简单易用的开源方案？来试试「DouDou」！**

**DouDou** 是基于 **Flet 框架**构建的现代化桌面语音助手，专为中文用户打造。它完全开源免费，数据本地处理，专为中文优化，支持国产AI模型。

### 🙏 致谢与致意

本项目基于优秀的开源项目 [QuQu (蛐蛐)](https://github.com/yan5xu/ququ) 进行了大量改进和重构。感谢原作者 Yan5Xu 提供的宝贵基础和开源精神。

**主要改进包括：**
- 🏗️ **架构重构**: 从单体文件重构为模块化架构，提高代码可维护性
- 🎯 **算法优化**: 针对中文语音优化的VAD系统，提升识别准确性
- 🖥️ **界面升级**: 现代化UI设计，支持实时连续识别显示
- 🔧 **技术栈升级**: 更新依赖库，修复兼容性问题
- 📊 **功能增强**: 增加设备管理、音频可视化、调试工具等功能

### ✨ 核心特性

- 🎯 **顶尖中文识别**: 内置阿里巴巴 **FunASR Paraformer** 模型，在您的电脑本地运行
- 🔒 **隐私至上**: 所有语音数据都在本地处理，保护您的隐私安全
- 🚀 **轻量快速**: 基于 Flet 框架，启动迅速，资源占用低
- 🎨 **现代化界面**: 简洁美观的用户界面，操作直观
- 🌐 **开放AI生态**: 支持任何兼容 OpenAI API 的服务
- 🏗️ **模块化架构**: 采用清晰的分层设计，代码易于维护和扩展
- 🔄 **组件化设计**: UI组件可复用，支持快速开发和迭代

---

## ⚡ GPU 加速配置（可选）

DouDou 支持自动检测并配置 GPU 加速，识别速度可提升 **10-50 倍**。

**智能配置脚本**（推荐）：
```bash
python smart_gpu_setup.py
```

该脚本会：
- 🔍 自动检测 NVIDIA GPU 和 CUDA 版本
- 📊 分析当前 PyTorch 配置状态
- 🎯 推荐最佳匹配的 PyTorch CUDA 版本
- ✅ 仅在必要时才提示安装/升级（不会盲目卸载）

**支持的GPU**：
- NVIDIA RTX 30/40 系列（3060/3070/3080/4090 等）
- NVIDIA GTX 10/16 系列
- 其他支持 CUDA 11.8+ 的 NVIDIA GPU

**性能提升**：
- 模型加载：13秒 → 3-5秒
- 识别速度：提升 10-50 倍
- 实时响应：低延迟，流畅体验

详细配置说明：[GPU 配置指南](docs/GPU_SETUP_GUIDE.md)

---

## 🚀 快速开始

### 1. 环境要求
- **Python 3.11+**
- **Windows 10+**, **macOS 10.15+**, 或 **Linux**
- （可选）NVIDIA GPU + CUDA 11.8+ 用于加速

### 2. 安装和运行

```bash
# 1. 克隆项目
git clone https://github.com/yan5xu/ququ.git
cd ququ

# 2. 创建虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 3. 安装依赖
pip install -e .

# 4. 运行应用
python main.py
```

#### 使用启动脚本 (Windows)

- **标准启动**: 双击 `run.bat` 文件即可启动应用
- **管理员权限启动**: 如果遇到音频驱动问题，双击 `run_as_admin.bat` 文件以管理员权限启动（可以解决Windows音频设备兼容性问题）

### 3. 配置AI模型

启动应用后，在设置中填入您的AI服务商提供的 **API Key**、**Base URL** 和 **模型名称**。支持通义千问、Kimi、智谱AI等国产模型。

## 🛠️ 技术栈

- **UI框架**: Flet
- **语音识别**: FunASR (Paraformer-large, FSMN-VAD, CT-Transformer)
- **AI模型**: 兼容 OpenAI, Anthropic, 阿里云通义千问, Kimi 等
- **音频处理**: PyAudio, NumPy, Librosa

## 📁 项目结构

```
ququ_flet/
├── main.py             # 应用入口文件
├── src/                # 源代码目录
│   ├── flet_app.py         # 主应用（协调器模式）
│   ├── core/               # 核心业务逻辑
│   │   ├── audio_engine.py      # 音频引擎
│   │   ├── audio_recorder.py   # 录音管理器
│   │   ├── transcription_handler.py  # 转写处理器
│   │   ├── vad_system.py       # 语音活动检测
│   │   ├── ai_integration.py   # AI集成
│   │   └── recognition_pipeline.py  # 识别流水线
│   ├── ui/                 # 用户界面
│   │   ├── components.py       # UI组件
│   │   └── dialogs.py          # 对话框
│   ├── utils/              # 工具模块
│   │   ├── config_manager.py   # 配置管理
│   │   └── audio_utils.py      # 音频工具
│   └── funasr_server.py    # FunASR 服务
├── download_models.py   # 模型下载脚本
├── run.bat             # Windows 启动脚本
├── run_as_admin.bat    # 管理员权限启动脚本
├── pyproject.toml      # Python 项目配置
├── requirements.txt    # 依赖列表
├── assets/            # 图标资源
└── README.md          # 项目说明
```

## 🤝 参与贡献

我们是一个开放和友好的社区，欢迎任何形式的贡献！

### 如何参与

- 🤔 **提建议**: 对产品有任何想法？欢迎到 [Issues](https://github.com/yan5xu/ququ/issues) 页面提出。
- 🐛 **报Bug**: 发现程序出错了？请毫不犹豫地告诉我们。
- 💻 **贡献代码**: 如果您想添加新功能或修复Bug，请参考以下步骤：
    1.  Fork 本项目
    2.  创建您的特性分支 (`git checkout -b feature/your-amazing-feature`)
    3.  提交您的更改 (`git commit -m 'feat: Add some amazing feature'`)
    4.  将您的分支推送到远程 (`git push origin feature/your-amazing-feature`)
    5.  创建一个 Pull Request

## 📦 打包分发

### Windows 平台打包 ✅

DouDou 支持 Windows 平台打包，可以生成独立的可执行文件，无需安装Python环境即可运行。

#### 快速打包

```bash
# 一键打包（推荐）
build_windows.bat
```

#### 手动打包

```bash
# 安装打包依赖
pip install -r build/pyinstaller/build_requirements.txt

# 运行打包脚本
python build/pyinstaller/build.py
```

#### 打包输出

打包完成后，会在 `release/` 目录生成：
- `DouDou.exe` - 独立可执行文件
- `DouDou-Windows-x64-v1.0.0.zip` - 完整发布包
- 配置文件和启动脚本

#### 平台兼容性说明

- ✅ **Windows**: 完整支持，已测试
- ⚠️ **macOS**: 理论支持，但缺少macOS设备进行测试
- ⚠️ **Linux**: 理论支持，但缺少Linux桌面环境进行测试

> **注意**: 由于开发者只有Windows设备，目前只能确保Windows平台的打包质量。欢迎社区用户测试其他平台并提供反馈。

### 跨平台构建计划

未来计划通过GitHub Actions实现真正的跨平台自动构建：

```yaml
# .github/workflows/build.yml
# 支持 Windows、macOS、Linux 三平台自动构建
```

## 🙏 致谢

本项目的诞生离不开以下优秀项目的启发和支持：

- [FunASR](https://github.com/modelscope/FunASR): 阿里巴巴开源的工业级语音识别工具包。
- [Flet](https://flet.dev/): 现代化的 Python UI 框架。
- [PyInstaller](https://pyinstaller.org/): Python应用打包工具。

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。