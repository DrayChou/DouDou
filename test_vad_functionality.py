#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAD系统功能测试脚本
"""

import sys
import os
import time
import numpy as np
from pathlib import Path

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.vad_system import VADConfig, HybridVADSegmenter

def generate_silence(duration: float, sample_rate: int = 16000) -> np.ndarray:
    """生成静音音频"""
    samples = int(sample_rate * duration)
    return np.zeros(samples, dtype=np.int16)

def generate_tone(duration: float, frequency: float = 440.0, amplitude: float = 12000.0, sample_rate: int = 16000) -> np.ndarray:
    """生成单音音频"""
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    return tone.astype(np.int16)

def test_vad_basic_functionality():
    """测试VAD基本功能"""
    print("=== VAD基本功能测试 ===")

    # 创建配置
    config = VADConfig.create_custom_config(
        MIN_SPEECH_DURATION=0.2,
        SILENCE_TIMEOUT=0.5,
        MAX_WINDOW_SIZE=3.0,
        ENERGY_THRESHOLD=300,
        ZCR_THRESHOLD=0.05,
        SMOOTHING_WINDOW=3,
        CONFIDENCE_THRESHOLD=0.5,
        OVERLAP_DURATION=0.1,
        MAX_BUFFER_DURATION=5.0,
    )

    print(f"VAD配置:")
    print(f"  - 最小语音时长: {config.MIN_SPEECH_DURATION}s")
    print(f"  - 静音超时: {config.SILENCE_TIMEOUT}s")
    print(f"  - 最大窗口: {config.MAX_WINDOW_SIZE}s")
    print(f"  - 能量阈值: {config.ENERGY_THRESHOLD}")
    print(f"  - 过零率阈值: {config.ZCR_THRESHOLD}")
    print(f"  - 置信度阈值: {config.CONFIDENCE_THRESHOLD}")

    # 创建VAD分段器
    segmenter = HybridVADSegmenter(sample_rate=16000, config=config)

    # 测试场景1: 静音->语音->静音
    print("\n--- 场景1: 静音->语音->静音 ---")
    chunks = [
        generate_silence(0.1),  # 静音
        generate_silence(0.1),  # 静音
        generate_tone(0.1, 440, 8000),  # 语音
        generate_tone(0.1, 440, 8000),  # 语音
        generate_tone(0.1, 440, 8000),  # 语音
        generate_tone(0.1, 440, 8000),  # 语音
        generate_silence(0.1),  # 静音
        generate_silence(0.1),  # 静音
        generate_silence(0.1),  # 静音
    ]

    segments = []
    for i, chunk in enumerate(chunks):
        segment, result = segmenter.process_chunk(chunk)

        print(f"帧{i+1}: 能量={result['energy']:.1f}, 过零率={result['zcr']:.3f}, "
              f"置信度={result['confidence']:.3f}, 检测到语音={result['is_voice']}, "
              f"应该处理={result['should_process']}")

        if segment:
            segments.append(segment)
            print(f"  >>> 检测到语音片段！时长: {segment.info['segment_duration']:.2f}s")

    print(f"总共检测到 {len(segments)} 个语音片段")

    # 测试场景2: 语音片段超出最大窗口
    print("\n--- 场景2: 长语音片段 ---")
    segmenter.reset()

    long_chunks = [generate_tone(0.1, 440, 8000) for _ in range(35)]  # 3.5秒

    segments = []
    for i, chunk in enumerate(long_chunks):
        segment, result = segmenter.process_chunk(chunk)

        if i % 5 == 0:  # 每5帧打印一次
            print(f"帧{i+1}: 语音={result['is_voice']}, 时长={result['speech_duration']:.2f}s, "
                  f"应该处理={result['should_process']}")

        if segment:
            segments.append(segment)
            print(f"  >>> 检测到语音片段！时长: {segment.info['segment_duration']:.2f}s")

    print(f"总共检测到 {len(segments)} 个语音片段")

    # 测试场景3: 短语音片段（应该被忽略）
    print("\n--- 场景3: 短语音片段 ---")
    segmenter.reset()

    short_chunks = [
        generate_silence(0.1),
        generate_tone(0.1, 440, 8000),  # 太短，应该被忽略
        generate_silence(0.1),
    ]

    segments = []
    for i, chunk in enumerate(short_chunks):
        segment, result = segmenter.process_chunk(chunk)
        print(f"帧{i+1}: 语音={result['is_voice']}, 时长={result['speech_duration']:.2f}s, "
              f"应该处理={result['should_process']}")

        if segment:
            segments.append(segment)

    print(f"总共检测到 {len(segments)} 个语音片段（预期为0）")

def test_vad_adaptive_threshold():
    """测试VAD自适应阈值"""
    print("\n=== 自适应阈值测试 ===")

    config = VADConfig.create_custom_config(
        MIN_SPEECH_DURATION=0.2,
        SILENCE_TIMEOUT=0.5,
        ENERGY_THRESHOLD=500,  # 初始阈值
        SMOOTHING_WINDOW=3,
        CONFIDENCE_THRESHOLD=0.5,
    )

    segmenter = HybridVADSegmenter(sample_rate=16000, config=config)

    # 先用低能量音频让系统适应
    print("--- 低能量适应阶段 ---")
    low_energy_chunks = [generate_tone(0.1, 440, 200) for _ in range(10)]

    for i, chunk in enumerate(low_energy_chunks):
        segment, result = segmenter.process_chunk(chunk)
        if i % 3 == 0:
            print(f"帧{i+1}: 能量={result['energy']:.1f}, 动态阈值={result['dynamic_threshold']:.1f}")

    # 再用高能量音频
    print("\n--- 高能量测试阶段 ---")
    high_energy_chunks = [generate_tone(0.1, 440, 8000) for _ in range(10)]

    for i, chunk in enumerate(high_energy_chunks):
        segment, result = segmenter.process_chunk(chunk)
        if i % 3 == 0:
            print(f"帧{i+1}: 能量={result['energy']:.1f}, 动态阈值={result['dynamic_threshold']:.1f}, "
                  f"检测到语音={result['is_voice']}")

def test_vad_statistics():
    """测试VAD统计信息"""
    print("\n=== VAD统计信息测试 ===")

    config = VADConfig()
    segmenter = HybridVADSegmenter(sample_rate=16000, config=config)

    # 生成混合音频
    mixed_chunks = []
    for i in range(20):
        if i < 5 or i >= 15:
            mixed_chunks.append(generate_silence(0.1))
        else:
            mixed_chunks.append(generate_tone(0.1, 440, 6000))

    # 处理音频
    for chunk in mixed_chunks:
        segment, result = segmenter.process_chunk(chunk)

    # 获取统计信息
    status = segmenter.get_status()
    vad_stats = segmenter.vad.get_statistics()

    print("VAD统计信息:")
    print(f"  - 总帧数: {vad_stats['total_frames']}")
    print(f"  - 语音帧数: {vad_stats['voice_frames']}")
    print(f"  - 语音比例: {vad_stats['voice_ratio']:.2%}")
    print(f"  - 语音段落数: {vad_stats['speech_segments']}")
    print(f"  - 平均能量: {vad_stats['avg_energy']:.1f}")
    print(f"  - 当前状态: {vad_stats['current_state']}")

if __name__ == "__main__":
    try:
        test_vad_basic_functionality()
        test_vad_adaptive_threshold()
        test_vad_statistics()
        print("\n=== VAD测试完成 ===")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()