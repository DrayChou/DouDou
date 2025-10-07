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
- 🤖 **智能文本处理**: AI修正识别错误，自动添加标点
- 🌍 **自动翻译**: 支持多语言翻译，可配置独立API
- 📝 **自定义Prompt**: 灵活的提示词配置，满足个性化需求
- 📊 **任务监控**: 实时显示处理状态和统计信息
- 📄 **完整日志**: 所有操作自动记录到日志文件，便于调试

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
- **Python 3.11+** (推荐 3.13)
- **Windows 10+**, **macOS 10.15+**, 或 **Linux**
- （可选）NVIDIA GPU + CUDA 11.8+ 用于加速

### 2. 安装和运行

```bash
# 1. 克隆项目
git clone https://github.com/DrayChou/DouDou.git
cd DouDou

# 2. 创建虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 下载FunASR模型（首次运行）
python download_models.py

# 5. 运行应用
python main.py
```

#### 使用启动脚本 (Windows - 推荐)

项目提供了便捷的Windows启动脚本，自动处理环境配置：

- **智能启动器**: 双击 `启动DouDou.bat` 文件（推荐）
  - ✅ 自动检测Python环境
  - ✅ 自动创建/激活虚拟环境
  - ✅ 自动安装依赖
  - ✅ 友好的用户界面和错误提示

- **快速启动**: 双击 `run.bat` 文件
  - 直接启动应用
  - 适合已配置好环境的用户

- **管理员权限启动**: 双击 `run_as_admin.bat` 文件
  - 解决Windows音频设备兼容性问题（Error -9999）
  - 需要访问WASAPI loopback设备时使用

> **提示**:
> - 首次使用建议使用`启动DouDou.bat`，它会自动完成所有配置
> - 如果遇到音频设备无法识别或录音失败，请尝试使用管理员权限启动

### 3. 配置AI服务

应用支持两种AI服务配置方式：

#### 方式1: 本地AI服务（推荐用于开发/隐私）
- 使用 [Jan Desktop](https://jan.ai/) 或其他本地LLM服务
- 默认配置: `http://localhost:11435/v1`
- 优点: 完全本地运行，数据隐私

#### 方式2: 云端AI服务
在设置中配置：
- **API Key**: 您的服务商API密钥
- **Base URL**: API端点地址
- **模型名称**: 使用的模型名称

支持的服务商：
- OpenAI (GPT-4, GPT-3.5)
- 通义千问 (Qwen)
- DeepSeek
- Kimi
- 智谱AI (GLM)

### 4. 新增功能配置

#### AI文本修正
- 自动修正语音识别错误
- 添加标点符号
- 优化表达流畅度
- 在设置 → 基础设置中启用

#### AI翻译
- 支持识别结果自动翻译
- 可配置目标语言（日语、英语等）
- 支持独立API配置或复用修正配置
- 在设置 → 翻译设置中配置

#### 自定义Prompt
- 支持自定义AI处理提示词
- 可保存为文件或内联配置
- 在设置 → Prompt设置中编辑

## 🛠️ 技术栈

- **UI框架**: Flet - Python跨平台桌面应用框架
- **语音识别**: FunASR (Paraformer-large, FSMN-VAD, CT-Transformer)
- **AI集成**: OpenAI兼容API，支持本地和云端服务
- **音频处理**: PyAudio/PyAudioWPatch, NumPy, Librosa
- **并发处理**: ThreadPoolExecutor多线程任务队列
- **日志系统**: Python logging + 文件轮转
- **配置管理**: JSON配置文件 + 分层继承机制

## 📁 项目结构

```
ququ_flet/
├── src/                    # 源代码目录
│   ├── flet_app.py            # 主应用入口
│   ├── core/                  # 核心业务逻辑
│   │   ├── audio_engine.py         # 音频引擎
│   │   ├── continuous_recorder.py  # 连续录音器
│   │   ├── vad_system.py           # VAD语音检测
│   │   ├── direct_funasr.py        # FunASR集成
│   │   ├── task_manager.py         # 多线程任务管理
│   │   └── task_processors/        # 任务处理器
│   │       ├── base_processor.py       # 处理器基类
│   │       ├── correction_processor.py # AI修正处理器
│   │       └── translation_processor.py # 翻译处理器
│   ├── ui/                    # 用户界面
│   │   ├── components.py           # UI组件库
│   │   ├── dialogs.py              # 对话框
│   │   ├── task_monitor.py         # 任务监控UI
│   │   └── enhanced_settings_dialog.py # 增强设置界面
│   └── utils/                 # 工具模块
│       ├── config_manager.py       # 配置管理
│       └── logger.py               # 日志系统
├── logs/                   # 日志文件目录
├── docs/                   # 文档目录
│   ├── config/                # 配置文件
│   └── *.md                   # 开发文档
├── tests/                  # 测试文件
├── download_models.py      # 模型下载脚本
├── run.bat                # Windows启动脚本
├── run_as_admin.bat       # 管理员权限启动
├── requirements.txt       # 依赖列表
└── README.md             # 项目说明
```

## 🔧 开发者指南

### 日志系统

应用使用统一的日志系统，所有日志会自动记录到 `logs/` 目录：

- `logs/ququ_YYYY-MM-DD.log` - 主日志文件（所有级别）
- `logs/ququ_error_YYYY-MM-DD.log` - 错误日志文件（仅ERROR及以上）

日志特性：
- 自动按日期分割
- 文件大小轮转（主日志10MB，错误日志5MB）
- 自动记录所有print输出
- 支持调试和生产环境

### 故障排查

#### AI功能无输出
1. 检查AI服务是否运行：
   ```bash
   curl http://localhost:11435/v1/models
   ```
2. 查看错误日志：`logs/ququ_error_*.log`
3. 确认配置文件中的API配置正确

#### 音频设备问题
- Windows Error -9999：使用 `run_as_admin.bat` 启动
- 设备无法识别：检查设备是否被其他程序占用
- 录音无声：确认选择了正确的输入设备

#### 窗口关闭后仍有进程
- 正常现象：监控线程需要时间清理
- 如需强制结束：`taskkill /F /IM python.exe`

### 测试

项目包含测试脚本用于验证功能：

```bash
# 测试修复功能
python test_fixes.py

# 测试AI修正任务
python test_correction.py

# 测试UI集成
python -m pytest tests/test_ui_integration.py -v
```

## 🚀 路线图

### 已完成 ✅
- [x] 模块化架构重构
- [x] AI文本修正功能
- [x] 多语言翻译支持
- [x] 自定义Prompt配置
- [x] 任务监控界面
- [x] 完整日志系统
- [x] 多线程任务队列

### 开发中 🚧
- [ ] 更多语言支持（英文、韩文等）
- [ ] 语音唤醒功能
- [ ] 历史记录管理
- [ ] 快捷键支持

### 计划中 📋
- [ ] 插件系统
- [ ] 云同步功能
- [ ] 跨平台打包（Windows/macOS/Linux）
- [ ] 语音合成（TTS）功能

## ⚠️ 已知限制

- **打包暂不支持**：由于Flet框架打包复杂性，暂时不提供打包版本，需要Python环境运行
- **平台测试**：主要在Windows平台测试，macOS和Linux支持待验证
- **GPU依赖**：GPU加速需要NVIDIA显卡和CUDA环境
- **模型大小**：FunASR模型较大（约1-2GB），首次运行需要下载
- **FFmpeg警告**：启动时可能出现FFmpeg扩展警告，不影响核心语音识别功能，可忽略

## 🤝 参与贡献

我们是一个开放和友好的社区，欢迎任何形式的贡献！

### 如何参与

- 🤔 **提建议**: 对产品有任何想法？欢迎到 [Issues](https://github.com/DrayChou/DouDou/issues) 页面提出。
- 🐛 **报Bug**: 发现程序出错了？请毫不犹豫地告诉我们（附上 `logs/` 目录中的日志）。
- 💻 **贡献代码**: 如果您想添加新功能或修复Bug，请参考以下步骤：
    1.  Fork 本项目
    2.  创建您的特性分支 (`git checkout -b feature/your-amazing-feature`)
    3.  提交您的更改 (`git commit -m 'feat: Add some amazing feature'`)
    4.  将您的分支推送到远程 (`git push origin feature/your-amazing-feature`)
    5.  创建一个 Pull Request

### 开发规范

- 遵循Python PEP 8编码规范
- 使用类型提示（Type Hints）
- 编写必要的文档和注释
- 提交前运行测试确保功能正常

## 🙏 致谢

本项目的诞生离不开以下优秀项目的启发和支持：

- [FunASR](https://github.com/modelscope/FunASR): 阿里巴巴开源的工业级语音识别工具包
- [Flet](https://flet.dev/): 现代化的 Python UI 框架
- [Jan](https://jan.ai/): 开源的本地AI运行环境
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/): Python音频处理库

特别感谢原项目 [QuQu (蛐蛐)](https://github.com/yan5xu/ququ) 提供的基础代码。

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。