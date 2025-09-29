<div align="center">

<!-- 在这里放置您的Logo图片 -->
<!-- 例如: <img src="assets/logo.png" width="150" /> -->
<br/>
<br/>

# 蛐蛐 (QuQu)

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

> **厌倦了复杂的语音输入工具？寻找简单易用的开源方案？来试试「蛐蛐」！**

**蛐蛐 (QuQu)** 是基于 **Flet 框架**构建的现代化桌面语音助手，专为中文用户打造。它完全开源免费，数据本地处理，专为中文优化，支持国产AI模型。

### ✨ 核心特性

- 🎯 **顶尖中文识别**: 内置阿里巴巴 **FunASR Paraformer** 模型，在您的电脑本地运行
- 🔒 **隐私至上**: 所有语音数据都在本地处理，保护您的隐私安全
- 🚀 **轻量快速**: 基于 Flet 框架，启动迅速，资源占用低
- 🎨 **现代化界面**: 简洁美观的用户界面，操作直观
- 🌐 **开放AI生态**: 支持任何兼容 OpenAI API 的服务

---

## 🚀 快速开始

### 1. 环境要求
- **Python 3.11+**
- **Windows 10+**, **macOS 10.15+**, 或 **Linux**

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
python flet_app.py
```

#### 使用启动脚本 (Windows)

双击 `run.bat` 文件即可启动应用。

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
├── flet_app.py          # 主应用文件
├── funasr_server.py     # FunASR 服务
├── download_models.py   # 模型下载脚本
├── run.bat             # Windows 启动脚本
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

## 🙏 致谢

本项目的诞生离不开以下优秀项目的启发和支持：

- [FunASR](https://github.com/modelscope/FunASR): 阿里巴巴开源的工业级语音识别工具包。
- [Flet](https://flet.dev/): 现代化的 Python UI 框架。

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。