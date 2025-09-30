#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连续录音器 - 支持实时模式的连续录音和VAD分段

独立线程运行，持续录音并通过VAD检测语音分段，
自动保存音频片段并提交到任务管理器。
"""

import os
import tempfile
import threading
import time
import wave
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable

from .audio_engine import AudioEngine
from .vad_system import HybridVADSegmenter, VADSegment
from .task_manager import TaskManager, AudioSegment

logger = logging.getLogger(__name__)


@dataclass
class RecorderConfig:
    """录音器配置"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: str = "int16"
    min_segment_duration: float = 0.5  # 最小片段时长（秒）
    max_segment_duration: float = 8.0   # 最大片段时长（秒）
    silence_timeout: float = 1.5        # 静音超时（秒）
    temp_dir: Optional[str] = None      # 临时目录


class ContinuousAudioRecorder:
    """连续录音器"""

    def __init__(self,
                 audio_engine: AudioEngine,
                 vad_segmenter: HybridVADSegmenter,
                 task_manager: TaskManager,
                 config: Optional[RecorderConfig] = None):
        """
        初始化连续录音器

        Args:
            audio_engine: 音频引擎
            vad_segmenter: VAD分段器
            task_manager: 任务管理器
            config: 录音器配置
        """
        self.audio_engine = audio_engine
        self.vad_segmenter = vad_segmenter
        self.task_manager = task_manager
        self.config = config or RecorderConfig()

        # 录音状态
        self.is_recording = False
        self.is_continuous = False
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

        # 录音线程
        self.recording_thread: Optional[threading.Thread] = None
        self.audio_stream = None

        # 音频数据缓冲
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()

        # 回调函数
        self.on_segment_detected: Optional[Callable[[AudioSegment], None]] = None
        self.on_recording_started: Optional[Callable[[], None]] = None
        self.on_recording_stopped: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        # 统计信息
        self.segments_count = 0
        self.start_time = 0.0
        self.total_duration = 0.0

        logger.info("ContinuousAudioRecorder 初始化完成")

    def start_continuous_recording(self) -> bool:
        """
        开始连续录音模式

        Returns:
            bool: 是否成功启动
        """
        if self.is_recording:
            logger.warning("录音已在进行中")
            return False

        try:
            # 重置状态
            self.is_recording = True
            self.is_continuous = True
            self.stop_event.clear()
            self.pause_event.clear()
            self.segments_count = 0
            self.start_time = time.time()
            self.total_duration = 0.0

            # 启动录音线程
            self.recording_thread = threading.Thread(
                target=self._continuous_recording_loop,
                name="ContinuousRecorder",
                daemon=True
            )
            self.recording_thread.start()

            logger.info("连续录音已启动")
            if self.on_recording_started:
                self.on_recording_started()

            return True

        except Exception as e:
            logger.error(f"启动连续录音失败: {e}")
            if self.on_error:
                self.on_error(e)
            return False

    def stop_continuous_recording(self):
        """停止连续录音"""
        if not self.is_recording:
            return

        logger.info("正在停止连续录音...")
        self.stop_event.set()
        self.is_recording = False
        self.is_continuous = False

        # 等待录音线程结束
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5.0)

        # 清理音频流
        if self.audio_stream:
            try:
                self.audio_engine.stop_stream(self.audio_stream)
                self.audio_stream = None
            except Exception as e:
                logger.error(f"停止音频流失败: {e}")

        logger.info("连续录音已停止")
        if self.on_recording_stopped:
            self.on_recording_stopped()

    def pause_recording(self):
        """暂停录音"""
        if self.is_recording and not self.pause_event.is_set():
            self.pause_event.set()
            logger.info("录音已暂停")

    def resume_recording(self):
        """恢复录音"""
        if self.is_recording and self.pause_event.is_set():
            self.pause_event.clear()
            logger.info("录音已恢复")

    def _continuous_recording_loop(self):
        """连续录音主循环"""
        try:
            # 打开音频流
            self.audio_stream = self.audio_engine.open_stream(
                sample_rate=self.config.sample_rate,
                channels=self.config.channels,
                chunk_size=self.config.chunk_size,
                format=self.config.format
            )

            logger.info("音频流已打开，开始连续录音")

            while not self.stop_event.is_set():
                # 检查暂停状态
                if self.pause_event.is_set():
                    time.sleep(0.1)
                    continue

                # 读取音频数据
                try:
                    chunk = self.audio_engine.read_chunk(self.audio_stream, timeout=0.1)
                    if chunk is None:
                        continue

                    # VAD处理
                    segment, vad_result = self.vad_segmenter.process_chunk(chunk)

                    if segment:
                        # 检测到语音片段，处理分段
                        self._process_voice_segment(segment, vad_result)

                except Exception as e:
                    logger.error(f"处理音频数据失败: {e}")
                    if self.on_error:
                        self.on_error(e)
                    time.sleep(0.1)
                    continue

        except Exception as e:
            logger.error(f"录音循环异常: {e}")
            if self.on_error:
                self.on_error(e)
        finally:
            # 清理
            if self.audio_stream:
                try:
                    self.audio_engine.stop_stream(self.audio_stream)
                except:
                    pass
                self.audio_stream = None

    def _process_voice_segment(self, segment: VADSegment, vad_result: dict):
        """处理语音片段"""
        try:
            # 保存音频文件
            audio_file = self._save_audio_segment(segment.audio)

            if audio_file:
                # 创建音频片段数据
                audio_segment = AudioSegment(
                    file_path=audio_file,
                    timestamp=time.time(),
                    duration=segment.info.get('segment_duration', 0.0),
                    segment_id=f"seg_{int(time.time() * 1000)}_{self.segments_count}",
                    vad_confidence=vad_result.get('confidence', 0.0),
                    sample_rate=self.config.sample_rate,
                    channels=self.config.channels,
                    metadata={
                        'vad_result': vad_result,
                        'segment_info': segment.info
                    }
                )

                # 更新统计
                self.segments_count += 1
                self.total_duration += audio_segment.duration

                logger.info(f"检测到语音片段 #{self.segments_count}: "
                          f"时长={audio_segment.duration:.2f}s, "
                          f"置信度={audio_segment.vad_confidence:.3f}")

                # 调用回调
                if self.on_segment_detected:
                    self.on_segment_detected(audio_segment)

                # 提交到任务管理器
                try:
                    self.task_manager.submit_audio_segment(audio_segment)
                except Exception as e:
                    logger.error(f"提交音频片段到任务管理器失败: {e}")

        except Exception as e:
            logger.error(f"处理语音片段失败: {e}")
            if self.on_error:
                self.on_error(e)

    def _save_audio_segment(self, audio_data) -> Optional[str]:
        """保存音频片段到临时文件"""
        try:
            # 确保临时目录存在
            temp_dir = self.config.temp_dir or tempfile.gettempdir()
            temp_dir = Path(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            segment_id = f"{int(time.time() * 1000)}_{self.segments_count}"
            filename = f"doudou_segment_{timestamp}_{segment_id}.wav"
            file_path = temp_dir / filename

            # 保存WAV文件
            with wave.open(str(file_path), 'wb') as wf:
                wf.setnchannels(self.config.channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.config.sample_rate)
                wf.writeframes(audio_data.tobytes())

            logger.debug(f"音频片段已保存: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"保存音频片段失败: {e}")
            return None

    def get_statistics(self) -> dict:
        """获取录音统计信息"""
        uptime = time.time() - self.start_time if self.start_time > 0 else 0
        return {
            'is_recording': self.is_recording,
            'is_continuous': self.is_continuous,
            'is_paused': self.pause_event.is_set(),
            'segments_count': self.segments_count,
            'total_duration': self.total_duration,
            'uptime': uptime,
            'average_segment_duration': self.total_duration / max(1, self.segments_count),
            'segments_per_minute': (self.segments_count / max(uptime / 60, 0.001))
        }

    def cleanup_temp_files(self, max_age_hours: int = 24):
        """清理临时音频文件"""
        try:
            temp_dir = Path(self.config.temp_dir or tempfile.gettempdir())
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            cleaned_count = 0
            for file_path in temp_dir.glob("doudou_segment_*.wav"):
                if current_time - file_path.stat().st_mtime > max_age_seconds:
                    file_path.unlink()
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"已清理 {cleaned_count} 个临时音频文件")

        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")

    def __del__(self):
        """析构函数"""
        if self.is_recording:
            self.stop_continuous_recording()