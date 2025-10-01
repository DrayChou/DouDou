#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR集成测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.recognition_pipeline import RecognitionPipeline

def test_funasr():
    """测试FunASR集成"""
    print("开始测试FunASR集成...")

    # 创建识别流水线
    pipeline = RecognitionPipeline(use_direct_integration=True)

    # 检查FunASR状态
    print("检查FunASR状态...")
    status = pipeline.check_funasr_status()
    print(f"FunASR状态: {status}")

    if not status.get("installed", False):
        print("FunASR未安装，请先安装: pip install funasr")
        return False

    if not status.get("initialized", False):
        print("FunASR未初始化，尝试初始化...")
        # 初始化会在这里自动进行

    # 创建一个简单的测试音频文件路径
    test_audio = "test_audio.wav"
    if not os.path.exists(test_audio):
        print(f"测试音频文件 {test_audio} 不存在，跳过实际转录测试")
        return True

    # 测试转录
    print(f"测试转录音频文件: {test_audio}")
    result = pipeline.transcribe_audio(test_audio)

    print(f"转录结果: {result}")

    if result.get("success"):
        print("✅ 转录测试成功")
        print(f"识别文本: {result.get('text', '')}")
        return True
    else:
        print("❌ 转录测试失败")
        print(f"错误: {result.get('error', '未知错误')}")
        return False

if __name__ == "__main__":
    test_funasr()