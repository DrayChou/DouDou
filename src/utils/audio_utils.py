#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频工具函数模块

提供音频处理、增强、格式转换等工具函数
"""

import numpy as np
from typing import List, Optional


def enhance_audio_quality(audio_frames: List[bytes], sample_rate: int = 16000) -> np.ndarray:
    """
    音频质量增强

    Args:
        audio_frames: 音频帧列表
        sample_rate: 采样率

    Returns:
        增强后的音频数据（归一化的float32数组）
    """
    try:
        # 将音频帧转换为numpy数组
        audio_data = b''.join(audio_frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0

        print(f"[AudioUtils] 开始音频增强，样本数: {len(audio_array)}")

        # 1. 噪音抑制
        audio_array = apply_noise_suppression(audio_array, sample_rate)

        # 2. 自动增益控制
        audio_array = apply_auto_gain_control(audio_array)

        # 3. 动态范围压缩
        audio_array = apply_dynamic_range_compression(audio_array)

        return audio_array

    except Exception as e:
        print(f"[AudioUtils] 音频增强失败: {e}")
        # 如果增强失败，返回原始数据
        audio_data = b''.join(audio_frames)
        return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0


def apply_noise_suppression(audio_array: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
    """
    噪音抑制 - 带通滤波器

    Args:
        audio_array: 音频数据
        sample_rate: 采样率

    Returns:
        滤波后的音频数据
    """
    try:
        from scipy import signal

        nyquist = sample_rate * 0.5
        # 语音频率范围 300-7000Hz
        low_freq = 300 / nyquist
        high_freq = 7000 / nyquist

        # 确保频率在有效范围内
        low_freq = max(0.01, min(0.99, low_freq))
        high_freq = max(0.01, min(0.99, high_freq))

        if low_freq >= high_freq:
            high_freq = 0.9
            low_freq = 0.1

        # 使用带通滤波器
        b, a = signal.butter(4, [low_freq, high_freq], btype='band')
        filtered_audio = signal.lfilter(b, a, audio_array)

        print(f"[AudioUtils] 噪音抑制完成")
        return filtered_audio

    except ImportError:
        print("[AudioUtils] scipy不可用，跳过噪音抑制")
        return audio_array
    except Exception as e:
        print(f"[AudioUtils] 噪音抑制失败: {e}")
        return audio_array


def apply_auto_gain_control(audio_array: np.ndarray, target_rms: float = 0.05) -> np.ndarray:
    """
    自动增益控制 - 归一化音量

    Args:
        audio_array: 音频数据
        target_rms: 目标RMS值

    Returns:
        增益调整后的音频数据
    """
    try:
        # 计算RMS音量
        rms = np.sqrt(np.mean(audio_array ** 2))

        if rms > 0:
            gain = target_rms / rms
            # 限制增益范围
            gain = np.clip(gain, 0.3, 2.0)
            audio_array = audio_array * gain
            print(f"[AudioUtils] 自动增益控制完成，增益: {gain:.2f}, RMS: {rms:.4f} -> {target_rms:.4f}")

        return audio_array

    except Exception as e:
        print(f"[AudioUtils] 自动增益控制失败: {e}")
        return audio_array


def apply_dynamic_range_compression(audio_array: np.ndarray, threshold: float = 0.5, ratio: float = 2.0) -> np.ndarray:
    """
    动态范围压缩

    Args:
        audio_array: 音频数据
        threshold: 压缩阈值
        ratio: 压缩比

    Returns:
        压缩后的音频数据
    """
    try:
        # 对超过阈值的部分进行温和压缩
        above_threshold = np.abs(audio_array) > threshold
        sign = np.sign(audio_array)
        abs_audio = np.abs(audio_array)

        # 压缩公式：output = threshold + (input - threshold) / ratio
        compressed = np.where(
            above_threshold,
            sign * (threshold + (abs_audio - threshold) / ratio),
            audio_array
        )

        compressed_count = np.sum(above_threshold)
        print(f"[AudioUtils] 动态范围压缩完成，压缩了 {compressed_count} 个样本")

        return compressed

    except Exception as e:
        print(f"[AudioUtils] 动态范围压缩失败: {e}")
        return audio_array


def get_audio_duration(audio_path: str) -> float:
    """
    获取音频文件时长

    Args:
        audio_path: 音频文件路径

    Returns:
        音频时长（秒）
    """
    try:
        import librosa
        duration = librosa.get_duration(path=audio_path)
        return duration
    except Exception:
        return 0.0


def calculate_rms_level(audio_data: np.ndarray) -> float:
    """
    计算音频RMS电平

    Args:
        audio_data: 音频数据

    Returns:
        RMS电平值
    """
    if len(audio_data) == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)))