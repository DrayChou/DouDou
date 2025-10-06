# DouDou 快速入门指南

## 📋 前置准备

### 必需
- Python 3.11 或更高版本（推荐 3.13）
- Windows 10+ / macOS 10.15+ / Linux

### 可选（用于GPU加速）
- NVIDIA GPU（RTX 30/40系列或GTX 10/16系列）
- CUDA 11.8 或更高版本

## 🚀 安装步骤

### 1. 获取代码

```bash
git clone https://github.com/DrayChou/DouDou.git
cd DouDou
```

### 2. 设置Python环境

#### Windows
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### macOS/Linux
```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 下载语音识别模型

```bash
python download_models.py
```

这将下载 FunASR 模型（约1-2GB），首次运行必需。

### 4. 配置GPU加速（可选）

```bash
python smart_gpu_setup.py
```

该脚本会自动检测GPU并配置最佳CUDA版本。

## 🎯 运行应用

### 方式1: 使用启动脚本（Windows推荐）

双击以下任一文件：
- `run.bat` - 标准启动
- `run_as_admin.bat` - 管理员权限启动（解决音频设备问题）

### 方式2: 命令行启动

```bash
# 确保虚拟环境已激活
cd src
python flet_app.py
```

## ⚙️ 配置AI服务

应用启动后，点击右下角的"设置"按钮进行配置。

### 选项A: 使用本地AI服务（推荐）

1. 下载并安装 [Jan Desktop](https://jan.ai/)
2. 启动Jan，确保服务运行在 `localhost:11435`
3. 在DouDou设置中使用默认配置即可

**优点**：
- ✅ 完全本地运行
- ✅ 数据隐私保护
- ✅ 无需API费用

### 选项B: 使用云端AI服务

在设置中填入：

**API配置**：
- API Key: 从服务商获取的密钥
- Base URL: API端点地址
- Model Name: 模型名称

**支持的服务商**：

| 服务商 | Base URL | 示例模型 |
|--------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | gpt-4, gpt-3.5-turbo |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-turbo |
| Kimi | `https://api.moonshot.cn/v1` | moonshot-v1-8k |

## 🎤 基本使用

### 录音模式

1. **单次录音**：
   - 点击"开始录音"按钮
   - 说话
   - 点击"停止录音"
   - 等待识别结果

2. **实时模式**（推荐）：
   - 启用"实时模式"开关
   - 点击"开始录音"
   - 持续说话，系统自动分段识别
   - 结果实时显示

### AI功能

#### 文本修正
在 设置 → 基础设置 中：
- 启用"AI优化"开关
- 系统将自动修正识别错误并优化标点

#### 翻译功能
在 设置 → 翻译设置 中：
- 启用"启用翻译"
- 选择目标语言（日语/英语等）
- 配置翻译API（可复用修正配置）

#### 自定义Prompt
在 设置 → Prompt设置 中：
- 编辑修正提示词
- 编辑翻译提示词
- 可保存为文件或直接配置

## 🔍 故障排查

### 音频问题

**Error -9999 (Windows)**
- 原因：音频驱动权限不足
- 解决：使用 `run_as_admin.bat` 启动

**设备未识别**
- 检查设备是否被占用
- 尝试重新插拔麦克风
- 在设置中手动选择设备

### AI功能无响应

**检查AI服务状态**：
```bash
curl http://localhost:11435/v1/models
```

**查看错误日志**：
- 打开 `logs/ququ_error_YYYY-MM-DD.log`
- 查找连接错误或API错误

**常见错误**：
- HTTP 502: AI服务未启动
- Connection refused: 服务地址错误
- Timeout: 网络或服务响应慢

### 性能问题

**识别速度慢**
1. 检查GPU是否启用：
   ```bash
   python smart_gpu_setup.py
   ```
2. 查看设备信息栏，确认显示"GPU (CUDA)"
3. 如使用CPU，考虑升级硬件

**内存占用高**
- FunASR模型较大，正常占用500MB-1GB
- 关闭不必要的其他应用
- 考虑使用GPU加速

## 📊 查看日志

应用运行时会自动记录日志到 `logs/` 目录：

```bash
# 查看主日志
tail -f logs/ququ_2025-10-03.log

# 查看错误日志
tail -f logs/ququ_error_2025-10-03.log
```

日志包含：
- 所有print输出
- 任务处理状态
- API调用详情
- 错误堆栈信息

## 🆘 获取帮助

遇到问题？可以：

1. **查看文档**：
   - [README.md](../README.md) - 项目总览
   - [GPU配置指南](GPU_SETUP_GUIDE.md) - GPU加速配置
   - [翻译功能使用](翻译功能使用示例.md) - 翻译功能详解

2. **提交Issue**：
   - 访问 [GitHub Issues](https://github.com/DrayChou/DouDou/issues)
   - 附上日志文件内容
   - 描述复现步骤

3. **社区讨论**：
   - 查看已有的Issue和讨论
   - 参与功能建议

## 🎉 开始使用

恭喜！您已经完成了DouDou的配置。

**下一步**：
- 🎤 尝试不同的录音模式
- 🤖 体验AI修正和翻译功能
- 📝 自定义Prompt以适应您的需求
- ⚡ 配置GPU加速提升性能

祝您使用愉快！
