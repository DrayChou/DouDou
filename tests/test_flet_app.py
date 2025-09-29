#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flet应用测试脚本
"""

import sys
import os
import subprocess
import tempfile
import wave
import numpy as np
from pathlib import Path

def test_dependencies():
    """测试依赖是否安装"""
    print("🧪 测试依赖安装...")

    try:
        import flet
        print(f"✅ Flet 版本: {flet.__version__}")
    except ImportError:
        print("❌ Flet 未安装")
        return False

    try:
        import pyaudio
        print(f"✅ PyAudio 版本: {pyaudio.__version__}")
    except ImportError:
        print("❌ PyAudio 未安装")
        return False

    try:
        import numpy
        print(f"✅ NumPy 版本: {numpy.__version__}")
    except ImportError:
        print("❌ NumPy 未安装")
        return False

    try:
        import funasr
        print(f"✅ FunASR 版本: {funasr.__version__}")
    except ImportError:
        print("❌ FunASR 未安装")
        return False

    return True

def test_audio_system():
    """测试音频系统"""
    print("\n🎵 测试音频系统...")

    try:
        import pyaudio
        audio = pyaudio.PyAudio()

        device_count = audio.get_device_count()
        print(f"✅ 音频设备数量: {device_count}")

        # 获取默认设备
        default_input = audio.get_default_input_device_info()
        print(f"✅ 默认输入设备: {default_input['name']}")

        audio.terminate()
        return True

    except Exception as e:
        print(f"❌ 音频系统测试失败: {str(e)}")
        return False

def test_funasr_server():
    """测试FunASR服务器"""
    print("\n🤖 测试FunASR服务器...")

    funasr_script = os.path.join(os.path.dirname(__file__), "funasr_server.py")

    if not os.path.exists(funasr_script):
        print("❌ FunASR服务器脚本不存在")
        return False

    try:
        # 测试状态检查
        test_input = {
            "action": "status"
        }

        result = subprocess.run(
            [sys.executable, funasr_script],
            input=json.dumps(test_input, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=30
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                if output.get("success"):
                    print("✅ FunASR服务器状态正常")
                    print(f"   - 已安装: {output.get('installed', False)}")
                    print(f"   - 已初始化: {output.get('initialized', False)}")
                    return True
                else:
                    print(f"⚠️ FunASR服务器状态异常: {output.get('error', '未知错误')}")
                    return False
            except json.JSONDecodeError:
                print("❌ FunASR服务器响应解析失败")
                return False
        else:
            print(f"❌ FunASR服务器执行失败: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ FunASR服务器响应超时")
        return False
    except Exception as e:
        print(f"❌ FunASR服务器测试失败: {str(e)}")
        return False

def create_test_audio():
    """创建测试音频文件"""
    print("\n🎵 创建测试音频文件...")

    try:
        # 生成1秒的静音音频
        sample_rate = 16000
        duration = 1
        frequency = 440  # A4音符

        # 生成正弦波
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.5

        # 转换为16位整数
        audio_data = (audio_data * 32767).astype(np.int16)

        # 创建临时WAV文件
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test_audio.wav")

        with wave.open(test_file, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        print(f"✅ 测试音频文件已创建: {test_file}")
        return test_file

    except Exception as e:
        print(f"❌ 创建测试音频失败: {str(e)}")
        return None

def test_transcription():
    """测试转录功能"""
    print("\n🎙️ 测试转录功能...")

    # 创建测试音频
    test_file = create_test_audio()
    if not test_file:
        return False

    try:
        funasr_script = os.path.join(os.path.dirname(__file__), "funasr_server.py")

        # 测试转录
        test_input = {
            "action": "transcribe",
            "audio_path": test_file,
            "options": {
                "use_vad": True,
                "use_punc": True,
                "language": "zh"
            }
        }

        result = subprocess.run(
            [sys.executable, funasr_script],
            input=json.dumps(test_input, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=60
        )

        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                if output.get("success"):
                    print("✅ 转录测试成功")
                    print(f"   - 识别文本: {output.get('text', '')[:50]}...")
                    print(f"   - 置信度: {output.get('confidence', 0.0):.2f}")
                    return True
                else:
                    print(f"⚠️ 转录测试失败: {output.get('error', '未知错误')}")
                    return False
            except json.JSONDecodeError:
                print("❌ 转录响应解析失败")
                return False
        else:
            print(f"❌ 转录测试失败: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ 转录测试超时")
        return False
    except Exception as e:
        print(f"❌ 转录测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试Flet应用...")
    print("=" * 50)

    tests = [
        ("依赖安装", test_dependencies),
        ("音频系统", test_audio_system),
        ("FunASR服务器", test_funasr_server),
        ("转录功能", test_transcription),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}测试...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name}测试失败")

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("✅ 所有测试通过，Flet应用可以正常运行!")
        print("\n启动应用:")
        print("python flet_app.py")
    else:
        print("❌ 部分测试失败，请检查相关组件")

    return passed == total

if __name__ == "__main__":
    import json
    success = main()
    sys.exit(0 if success else 1)