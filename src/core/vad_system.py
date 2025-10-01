#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAD (Voice Activity Detection) 语音活动检测系统

实现基于能量阈值、过零率和时间窗口的混合VAD策略，
提供音频缓冲管理和语音片段分段能力。
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class VADConfig:
    """语音活动检测配置"""

    # 时间窗口参数
    MIN_SPEECH_DURATION = 0.5  # 最短语音片段(秒)
    MAX_SPEECH_DURATION = 6.0  # 最长语音片段(秒) - 降低避免过长
    SILENCE_TIMEOUT = 1.0      # 静音超时触发处理(秒) - 更快截断
    MAX_WINDOW_SIZE = 8.0      # 强制分段的最大窗口(秒) - 降低

    # 能量检测参数
    ENERGY_THRESHOLD = 500     # 音频能量阈值
    SILENCE_ENERGY = 200       # 静音能量阈值
    ZCR_THRESHOLD = 0.1        # 过零率阈值

    # 平滑参数
    SMOOTHING_WINDOW = 5       # 平滑窗口帧数
    CONFIDENCE_THRESHOLD = 0.6 # 语音置信度阈值

    # 分段/缓冲参数
    OVERLAP_DURATION = 0.2     # 分段重叠时长(秒)
    MAX_BUFFER_DURATION = 12.0 # 缓冲区保留最大时长(秒)
    PROCESSING_DELAY = 0.25    # 允许的处理延迟(秒)

    @classmethod
    def create_custom_config(cls, **kwargs) -> "VADConfig":
        """创建自定义配置实例"""
        config = cls()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


class AudioBuffer:
    """音频缓冲区管理"""

    def __init__(self, sample_rate: int = 16000, max_duration_seconds: float = 10.0) -> None:
        self.sample_rate = sample_rate
        self.max_duration_seconds = max_duration_seconds
        self.buffer: List[int] = []
        self.timestamps: List[float] = []
        self.start_time = time.time()

    def append(self, audio_data: np.ndarray) -> None:
        if isinstance(audio_data, np.ndarray):
            self.buffer.extend(audio_data.astype(np.int16).tolist())
        else:
            self.buffer.extend(audio_data)
        self.timestamps.append(time.time())
        self._trim_to_max_duration()

    def get_duration(self) -> float:
        return len(self.buffer) / self.sample_rate

    def get_recent_data(self, duration_seconds: float) -> np.ndarray:
        samples_needed = int(duration_seconds * self.sample_rate)
        if len(self.buffer) <= samples_needed:
            return np.array(self.buffer, dtype=np.int16)
        return np.array(self.buffer[-samples_needed:], dtype=np.int16)

    def get_all_data(self) -> np.ndarray:
        return np.array(self.buffer, dtype=np.int16)

    def clear(self) -> None:
        self.buffer.clear()
        self.timestamps.clear()
        self.start_time = time.time()

    def get_buffer_info(self) -> Dict[str, Any]:
        return {
            "duration": self.get_duration(),
            "samples": len(self.buffer),
            "size_mb": len(self.buffer) * 2 / (1024 * 1024),
            "timestamps_count": len(self.timestamps),
        }

    def extract_segment(self, keep_tail_duration: float = 0.0) -> np.ndarray:
        segment = np.array(self.buffer, dtype=np.int16)

        if keep_tail_duration <= 0 or len(self.buffer) == 0:
            self.clear()
            return segment

        samples_to_keep = int(keep_tail_duration * self.sample_rate)
        samples_to_keep = max(0, min(samples_to_keep, len(self.buffer)))

        tail = self.buffer[-samples_to_keep:] if samples_to_keep else []
        tail_timestamps = self.timestamps[-samples_to_keep:] if self.timestamps else []

        self.buffer = list(tail)
        self.timestamps = list(tail_timestamps)
        self.start_time = time.time()
        return segment

    def _trim_to_max_duration(self) -> None:
        if self.max_duration_seconds <= 0:
            return

        max_samples = int(self.max_duration_seconds * self.sample_rate)
        if len(self.buffer) <= max_samples:
            return

        overflow = len(self.buffer) - max_samples
        self.buffer = self.buffer[overflow:]
        if self.timestamps:
            self.timestamps = self.timestamps[-len(self.buffer):]
        self.start_time = time.time()


class HybridVAD:
    """混合模式语音活动检测器"""

    def __init__(self, config: Optional[VADConfig] = None) -> None:
        self.config = config or VADConfig()
        self.energy_history: List[float] = []
        self.voice_confidence_history: List[float] = []
        self.is_speaking = False
        self.speech_start_time: Optional[float] = None
        self.last_voice_time: Optional[float] = None
        self.stats = {
            "total_frames": 0,
            "voice_frames": 0,
            "speech_segments": 0,
            "avg_energy": 0.0,
        }

    def calculate_energy(self, audio_data: np.ndarray) -> float:
        if len(audio_data) == 0:
            return 0.0
        return float(np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)))

    def calculate_zcr(self, audio_data: np.ndarray) -> float:
        if len(audio_data) <= 1:
            return 0.0
        zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
        return float(zero_crossings / len(audio_data))

    def _update_adaptive_threshold(self, energy: float) -> float:
        self.energy_history.append(energy)
        if len(self.energy_history) > 50:
            self.energy_history.pop(0)

        if len(self.energy_history) < 10:
            return self.config.ENERGY_THRESHOLD

        avg_energy = np.mean(self.energy_history)
        std_energy = np.std(self.energy_history)
        dynamic_threshold = max(self.config.ENERGY_THRESHOLD, avg_energy + 1.5 * std_energy)
        return float(dynamic_threshold)

    def detect_voice_activity(self, audio_data: np.ndarray) -> Dict[str, Any]:
        current_time = time.time()
        self.stats["total_frames"] += 1

        energy = self.calculate_energy(audio_data)
        zcr = self.calculate_zcr(audio_data)
        dynamic_threshold = self._update_adaptive_threshold(energy)

        energy_confidence = 1.0 if energy > dynamic_threshold else 0.0
        zcr_confidence = 1.0 if zcr > self.config.ZCR_THRESHOLD else 0.0
        # 中文语音优化：更重视能量检测，降低过零率权重
        voice_confidence = 0.8 * energy_confidence + 0.2 * zcr_confidence

        self.voice_confidence_history.append(voice_confidence)
        if len(self.voice_confidence_history) > self.config.SMOOTHING_WINDOW:
            self.voice_confidence_history.pop(0)

        smoothed_confidence = float(np.mean(self.voice_confidence_history))
        is_voice_detected = smoothed_confidence > self.config.CONFIDENCE_THRESHOLD

        if is_voice_detected:
            if not self.is_speaking:
                self.is_speaking = True
                self.speech_start_time = current_time
                self.stats["speech_segments"] += 1
                print(f"[VAD] 检测到语音开始，能量: {energy:.1f}, 阈值: {dynamic_threshold:.1f}")
            self.last_voice_time = current_time
            self.stats["voice_frames"] += 1

        self.stats["avg_energy"] = (
            (self.stats["avg_energy"] * (self.stats["total_frames"] - 1) + energy)
            / self.stats["total_frames"]
        )

        return {
            "is_voice": is_voice_detected,
            "energy": energy,
            "zcr": zcr,
            "confidence": smoothed_confidence,
            "dynamic_threshold": dynamic_threshold,
            "should_process": self._should_process_segment(current_time),
            "speech_duration": current_time - self.speech_start_time if self.speech_start_time else 0.0,
        }

    def _should_process_segment(self, current_time: float) -> bool:
        if not self.is_speaking:
            return False

        speech_duration = current_time - self.speech_start_time if self.speech_start_time else 0.0
        silence_duration = current_time - self.last_voice_time if self.last_voice_time else 0.0

        if speech_duration >= self.config.MAX_WINDOW_SIZE:
            print(f"[VAD] 达到最大窗口时长 {self.config.MAX_WINDOW_SIZE}s，强制处理")
            return True

        if (
            silence_duration >= self.config.SILENCE_TIMEOUT
            and speech_duration >= self.config.MIN_SPEECH_DURATION
        ):
            print(
                f"[VAD] 检测到语音结束，语音时长: {speech_duration:.1f}s，静音时长: {silence_duration:.1f}s"
            )
            return True

        return False

    def reset_state(self) -> None:
        self.is_speaking = False
        self.speech_start_time = None
        self.last_voice_time = None
        print("[VAD] 状态已重置")

    def get_statistics(self) -> Dict[str, Any]:
        voice_ratio = (
            self.stats["voice_frames"] / self.stats["total_frames"]
            if self.stats["total_frames"] > 0
            else 0.0
        )
        return {
            **self.stats,
            "voice_ratio": voice_ratio,
            "current_state": "speaking" if self.is_speaking else "silence",
            "energy_history_size": len(self.energy_history),
            "confidence_history_size": len(self.voice_confidence_history),
        }

    def configure(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                print(f"[VAD] 配置已更新: {key} = {value}")
            else:
                print(f"[VAD] 警告: 未知配置参数 {key}")


@dataclass
class VADSegment:
    """检测到的语音片段"""

    audio: np.ndarray
    info: Dict[str, Any]


class HybridVADSegmenter:
    """使用混合VAD策略的实时分段器"""

    def __init__(
        self,
        sample_rate: int = 16000,
        config: Optional[VADConfig] = None,
        overlap_duration: Optional[float] = None,
        max_buffer_duration: Optional[float] = None,
    ) -> None:
        self.config = config or VADConfig()
        self.sample_rate = sample_rate
        self.overlap_duration = max(
            0.0,
            overlap_duration if overlap_duration is not None else self.config.OVERLAP_DURATION,
        )
        buffer_duration = (
            max_buffer_duration if max_buffer_duration is not None else self.config.MAX_BUFFER_DURATION
        )

        self.buffer = AudioBuffer(sample_rate=sample_rate, max_duration_seconds=buffer_duration)
        self.vad = HybridVAD(self.config)
        self.last_result: Optional[Dict[str, Any]] = None
        self.on_segment_detected: Optional[Callable[[VADSegment], None]] = None

    def process_chunk(self, chunk) -> Tuple[Optional[VADSegment], Dict[str, Any]]:
        audio_array = self._normalize_chunk(chunk)
        if audio_array.size == 0:
            empty_result = {
                "is_voice": False,
                "energy": 0.0,
                "zcr": 0.0,
                "confidence": 0.0,
                "dynamic_threshold": self.config.ENERGY_THRESHOLD,
                "should_process": False,
                "speech_duration": 0.0,
            }
            self.last_result = empty_result
            return None, empty_result

        self.buffer.append(audio_array)
        vad_result = self.vad.detect_voice_activity(audio_array)

        segment: Optional[VADSegment] = None
        if vad_result["should_process"]:
            segment_audio = self.buffer.extract_segment(self.overlap_duration)
            segment_info = {
                **vad_result,
                "segment_duration": len(segment_audio) / self.sample_rate,
                "timestamp": time.time(),
                "buffer_duration": self.buffer.get_duration(),
            }
            segment = VADSegment(audio=segment_audio, info=segment_info)

            # 触发分段检测回调
            if self.on_segment_detected:
                self.on_segment_detected(segment)

            self.vad.reset_state()

        self.last_result = vad_result
        return segment, vad_result

    def reset(self) -> None:
        self.buffer.clear()
        self.vad.reset_state()
        self.last_result = None

    def get_status(self) -> Dict[str, Any]:
        status = {
            "overlap_duration": self.overlap_duration,
            "buffer": self.buffer.get_buffer_info(),
        }
        if self.last_result is not None:
            status["last_vad"] = self.last_result
        return status

    def _normalize_chunk(self, chunk) -> np.ndarray:
        if isinstance(chunk, np.ndarray):
            return chunk.astype(np.int16, copy=False).ravel()
        if isinstance(chunk, (bytes, bytearray)):
            return np.frombuffer(chunk, dtype=np.int16)
        return np.array(chunk, dtype=np.int16).ravel()


def create_chinese_optimized_config() -> VADConfig:
    """创建针对中文语音优化的VAD配置"""
    config = VADConfig()

    # 降低置信度阈值，提高敏感度
    config.CONFIDENCE_THRESHOLD = 0.4  # 从0.6降到0.4

    # 减少平滑窗口，提高响应速度
    config.SMOOTHING_WINDOW = 3  # 从5降到3

    # 调整权重分配，更重视能量检测
    # 注意：这需要在HybridVAD类中修改权重

    # 针对中文语音调整时间参数
    config.SILENCE_TIMEOUT = 2.0  # 从1.5s增加到2.0s，适应中文的自然停顿
    config.MIN_SPEECH_DURATION = 0.3  # 从0.5s降到0.3s，捕捉更短的中文音节

    # 调整过零率阈值，适应中文声调
    config.ZCR_THRESHOLD = 0.08  # 从0.1降到0.08，对中文声调更敏感

    return config


def create_english_optimized_config() -> VADConfig:
    """创建针对英文语音优化的VAD配置"""
    config = VADConfig()

    # 英文语音可以使用相对较高的置信度阈值
    config.CONFIDENCE_THRESHOLD = 0.5

    # 适中的平滑窗口
    config.SMOOTHING_WINDOW = 4

    # 英文语音的时间参数
    config.SILENCE_TIMEOUT = 1.2
    config.MIN_SPEECH_DURATION = 0.4

    # 英文语音的过零率阈值
    config.ZCR_THRESHOLD = 0.12

    return config
