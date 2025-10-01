# DouDou Flet 版本 - 标准 Python 虚拟环境设置指南

## 🐍 使用标准 Python 虚拟环境

我们现在使用标准的 `python -m venv` 而不是 uv 来管理依赖。

### 📦 环境设置步骤

#### 1. 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Linux/macOS)
source .venv/bin/activate
```

#### 2. 安装依赖
```bash
# 升级 pip
python -m pip install --upgrade pip

# 安装核心依赖
pip install flet>=0.28.3 pyaudio>=0.2.14 numpy>=1.21.0

# 安装 FunASR 相关依赖
pip install funasr>=1.2.7 librosa>=0.10.0 torch>=2.0.0 torchaudio>=2.0.0 modelscope>=1.9.0

# 或一次性安装所有依赖
pip install -r requirements.txt
```

#### 3. 下载模型文件
```bash
# 下载 FunASR 模型
python download_models.py
```

#### 4. 运行应用
```bash
# 启动 Flet 应用
python flet_app.py
```

### 🔧 故障排除

#### PyAudio 安装问题
如果遇到 PyAudio 安装问题：

**Windows:**
```bash
# 使用预编译的轮子
pip install pipwin
pipwin install pyaudio

# 或者直接下载 whl 文件
pip install https://www.lfd.uci.edu/~gohlke/pythonlibs/pyaudio
```

**macOS:**
```bash
# 使用 Homebrew
brew install portaudio
pip install pyaudio
```

**Ubuntu/Debian:**
```bash
# 安装系统依赖
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

#### 网络问题
如果下载模型或安装依赖遇到网络问题：
```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ flet pyaudio numpy

# ModelScope 镜像配置
export MODELSCOPE_CACHE_DIR=~/.cache/modelscope
```

### 📋 依赖列表

核心依赖包括：
- `flet>=0.28.3` - 现代化 Python UI 框架
- `pyaudio>=0.2.14` - 音频录制和播放
- `numpy>=1.21.0` - 数值计算
- `funasr>=1.2.7` - 阿里巴巴语音识别
- `librosa>=0.10.0` - 音频处理
- `torch>=2.0.0` - PyTorch 深度学习框架
- `torchaudio>=2.0.0` - PyTorch 音频处理
- `modelscope>=1.9.0` - 模型下载和管理

### 🚀 快速启动脚本

我们提供了多个启动脚本：
- `run_with_system_python.bat` - Windows 批处理脚本
- `launch.ps1` - PowerShell 脚本
- `run.sh` - Bash 脚本（Linux/macOS）

### 📂 项目结构

```
ququ_flet/
├── flet_app.py                    # 主应用文件
├── funasr_server.py              # FunASR 语音识别服务器
├── download_models.py            # 模型下载脚本
├── requirements.txt              # Python 依赖列表
├── .venv/                        # Python 虚拟环境（自动创建）
├── run_with_system_python.bat   # Windows 启动脚本
├── launch.ps1                   # PowerShell 启动脚本
├── run.sh                       # Bash 启动脚本
└── README_FLET.md               # 详细文档
```

### ✅ 验证安装

```bash
# 检查依赖是否正确安装
python -c "import flet; import pyaudio; import numpy; import funasr; print('所有依赖安装成功！')"

# 运行基本测试
python simple_test.py

# 启动应用
python flet_app.py
```

---

**注意**: 我们已经移除了 `pyproject.toml` 和 uv 相关配置，现在使用标准的 Python 虚拟环境管理。这样更简单，兼容性更好。