# GPU 加速配置指南

## 问题诊断

如果您的系统有NVIDIA GPU，但DouDou仍使用CPU模式，通常是因为PyTorch安装的是CPU版本。

### 检查当前状态

```bash
# 检查PyTorch版本
python -c "import torch; print('PyTorch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available())"

# 检查GPU状态
nvidia-smi
```

**正常输出示例（GPU已启用）**：
```
PyTorch版本: 2.8.0+cu126
CUDA可用: True
```

**问题输出示例（仅CPU）**：
```
PyTorch版本: 2.8.0+cpu
CUDA可用: False
```

## 解决方案

### 方法1: 使用智能检测脚本（推荐）

**运行智能GPU配置脚本**：

```bash
python smart_gpu_setup.py
```

**该脚本会智能检测并自动配置GPU环境**：

#### 检测流程
1. **GPU硬件检测**
   - 自动识别NVIDIA GPU型号（如RTX 3060/3070/4090）
   - 读取驱动版本和显存信息
   - 提取CUDA版本（从nvidia-smi）

2. **PyTorch状态分析**
   - 检查虚拟环境中的PyTorch版本
   - 判断CUDA支持状态（是否GPU可用）
   - 对比当前版本与硬件推荐版本

3. **智能决策引擎**
   - ✅ **版本已匹配** → 显示"无需操作"，保持现状
   - 🔄 **版本不匹配** → 显示当前vs推荐，建议升级
   - ❌ **CPU版本** → 提示安装CUDA版本，说明性能提升
   - 📦 **未安装** → 推荐适配的CUDA版本（cu118/cu126等）

4. **安全执行流程**
   - 显示详细的配置对比和下载大小
   - **等待用户确认** 后才执行操作（不会盲目卸载）
   - 完成后自动验证安装结果

#### CUDA版本自动映射

脚本会根据检测到的CUDA版本自动选择匹配的PyTorch：

| CUDA驱动版本 | PyTorch索引 | 适用GPU |
|-------------|-------------|---------|
| 11.8 | cu118 | GTX 1060/1070/1080系列 |
| 12.1 | cu121 | RTX 20系列 |
| 12.4 | cu124 | RTX 30系列 |
| 12.6 | cu126 | RTX 30/40系列（推荐） |
| 12.8 | cu128 | 最新驱动 |

#### 使用示例

```bash
# 在项目根目录运行
D:\Code\ququ_flet> python smart_gpu_setup.py

============================================================
DouDou - 智能GPU配置检测
============================================================

[1/5] 检测GPU硬件...
✅ 检测到GPU: NVIDIA GeForce RTX 3070
    驱动版本: 560.94
    显存: 8192 MiB

[2/5] 检测CUDA版本...
✅ CUDA版本: 12.6
    推荐PyTorch索引: cu126

[3/5] 检测虚拟环境中的PyTorch...
❌ 当前PyTorch版本: 2.0.1 (无CUDA支持)

[4/5] 配置建议...
⚠️  建议升级PyTorch以匹配CUDA版本

当前版本: 2.0.1 (CUDA N/A)
建议版本: 2.8.0 (CUDA cu126)

确认升级? (Y/N):
```

### 方法2: 手动安装

#### 步骤1: 卸载CPU版本

```bash
pip uninstall -y torch torchvision torchaudio
```

#### 步骤2: 安装CUDA版本

根据您的CUDA驱动版本选择：

**CUDA 12.6** (RTX 3060/3070/3080/3090/4090等):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

**CUDA 12.4**:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**CUDA 11.8** (旧版GPU):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 步骤3: 验证安装

```bash
python -c "import torch; print('CUDA可用:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

预期输出：
```
CUDA可用: True
GPU: NVIDIA GeForce RTX 3070
```

## 性能对比

安装CUDA版本后，DouDou的性能提升显著：

| 模式 | 模型加载时间 | 识别速度 | 实时性 |
|------|-------------|---------|--------|
| CPU | 13-20秒 | 1x (基准) | 一般 |
| GPU | 3-5秒 | 10-50x | 优秀 |

## 验证DouDou GPU加速

启动DouDou后，检查界面中部的设备信息：

```
音频设备: Microphone (USB) | 计算设备: 🚀 GPU (CUDA)
```

如果显示 `💻 CPU`，说明仍在使用CPU模式。

## 故障排除

### 问题1: CUDA版本不匹配

**症状**：安装后仍显示 `CUDA可用: False`

**解决**：
1. 检查CUDA驱动版本：`nvidia-smi` (右上角显示CUDA Version)
2. 安装对应的PyTorch版本（见上方安装命令）

### 问题2: 显存不足

**症状**：运行时出现 `CUDA out of memory` 错误

**解决**：
1. 关闭其他使用GPU的程序（浏览器、游戏等）
2. 降低batch_size参数（在代码中调整）

### 问题3: 多GPU选择

**症状**：系统有多个GPU，想指定使用哪个

**解决**：
DouDou自动使用GPU 0，如需更改，编辑 `src/core/direct_funasr.py`:

```python
# 修改 _detect_device() 方法
if torch.cuda.is_available():
    return "cuda:1"  # 使用第二个GPU
```

## 相关资源

- [PyTorch官方安装指南](https://pytorch.org/get-started/locally/)
- [NVIDIA CUDA下载](https://developer.nvidia.com/cuda-downloads)
- [FunASR GPU文档](https://github.com/modelscope/FunASR)

## 测试工具

项目提供设备检测测试脚本：

```bash
python test_device_detection.py
```

输出详细的设备信息、GPU规格、显存等。
