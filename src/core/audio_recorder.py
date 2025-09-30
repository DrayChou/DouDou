#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
录音处理模块

处理录音线程、音频文件保存、音频增强等功能
"""

import os
import time
import wave
import tempfile
import threading
import numpy as np
from datetime import datetime
from typing import List, Optional, Callable
from pathlib import Path

from .audio_engine import AudioEngine, AudioStreamConfig
from utils.audio_utils import enhance_audio_quality, calculate_rms_level


class AudioRecorder:
    """音频录音管理器"""

    def __init__(self, audio_engine: AudioEngine):
        """
        初始化录音管理器

        Args:
            audio_engine: 音频引擎实例
        """
        self.engine = audio_engine
        self.is_recording = False
        self.recording_thread: Optional[threading.Thread] = None
        self.progress_thread: Optional[threading.Thread] = None
        self.audio_frames: List[bytes] = []
        self.current_audio_file: Optional[str] = None
        self.start_time: float = 0
        self.device_index: Optional[int] = None

        # 回调函数
        self.on_progress_update: Optional[Callable[[str, float], None]] = None
        self.on_audio_data: Optional[Callable[[bytes, float], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_recording_started: Optional[Callable[[], None]] = None
        self.on_recording_stopped: Optional[Callable[[str], None]] = None
        self.on_audio_level_update: Optional[Callable[[float], None]] = None

    def start_recording(self, stream_config: AudioStreamConfig) -> bool:
        """
        开始录音

        Args:
            stream_config: 音频流配置

        Returns:
            bool: 是否成功开始
        """
        if self.is_recording:
            return False

        try:
            self.audio_frames = []
            self.is_recording = True
            self.start_time = time.time()

            # 触发录音开始回调
            if self.on_recording_started:
                self.on_recording_started()

            # 启动录音线程
            self.recording_thread = threading.Thread(
                target=self._recording_worker,
                args=(stream_config,),
                daemon=True
            )
            self.recording_thread.start()

            # 启动进度线程
            self.progress_thread = threading.Thread(
                target=self._progress_worker,
                daemon=True
            )
            self.progress_thread.start()

            self.update_status("录音已开始")
            return True

        except Exception as e:
            print(f"[AudioRecorder] 开始录音失败: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[str]:
        """
        停止录音并保存文件

        Returns:
            Optional[str]: 保存的音频文件路径，失败返回None
        """
        self.is_recording = False

        # 等待线程结束
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2)

        if self.progress_thread and self.progress_thread.is_alive():
            self.progress_thread.join(timeout=1)

        # 保存音频文件
        audio_file = None
        if self.audio_frames:
            audio_file = self.save_audio_file()

        # 触发录音停止回调
        if self.on_recording_stopped:
            self.on_recording_stopped(audio_file)

        return audio_file

    def _recording_worker(self, stream_config: AudioStreamConfig):
        """录音工作线程"""
        print(f"[AudioRecorder] 录音线程开始")

        stream = None
        frame_count = 0

        try:
            stream = self.engine.open_input_stream(stream_config, start=True)

            while self.is_recording:
                try:
                    data = stream.read(stream_config.chunk, exception_on_overflow=False)

                    if data and self.is_recording:
                        self.audio_frames.append(data)
                        frame_count += 1

                        # 计算音频电平并触发回调
                        if frame_count % 5 == 0:
                            audio_data = np.frombuffer(data, dtype=np.int16)
                            rms_level = calculate_rms_level(audio_data)

                            # 触发音频数据回调
                            if self.on_audio_data:
                                self.on_audio_data(data, rms_level)

                            # 触发音频级别更新回调
                            if self.on_audio_level_update:
                                self.on_audio_level_update(rms_level)

                except Exception as e:
                    print(f"[AudioRecorder] 读取音频数据失败: {e}")
                    time.sleep(0.01)

        except Exception as e:
            print(f"[AudioRecorder] 录音线程异常: {e}")

        finally:
            if stream:
                self.engine.close_stream(stream)
            print(f"[AudioRecorder] 录音线程结束，共 {frame_count} 帧")

    def _progress_worker(self):
        """进度更新工作线程"""
        start_time = time.time()

        while self.is_recording:
            elapsed = time.time() - start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)

            # 触发进度回调
            if self.on_progress_update:
                status_text = f"正在录音... {minutes:02d}:{seconds:02d}"
                progress_value = (elapsed % 2) / 2  # 脉冲效果
                self.on_progress_update(status_text, progress_value)

            time.sleep(0.1)

    def save_audio_file(self, enhance: bool = False) -> Optional[str]:
        """
        保存音频文件

        Args:
            enhance: 是否进行音频增强

        Returns:
            Optional[str]: 保存的文件路径
        """
        if not self.audio_frames:
            print("[AudioRecorder] 没有音频数据可保存")
            return None

        try:
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            print(f"[AudioRecorder] 开始保存音频，帧数: {len(self.audio_frames)}")

            # 计算音频信息
            total_bytes = sum(len(frame) for frame in self.audio_frames)
            # 正确计算时长：总字节数 / (采样率 * 通道数 * 每个采样字节数)
            bytes_per_second = self.engine.sample_rate * self.engine.channels * 2  # 16-bit = 2 bytes
            duration = total_bytes / bytes_per_second
            print(f"[AudioRecorder] 音频信息: {total_bytes} bytes, {duration:.2f}秒, 采样率: {self.engine.sample_rate}, 通道: {self.engine.channels}")

            # 保存原始音频
            original_file = os.path.join(temp_dir, f"ququ_recording_original_{timestamp}.wav")
            print(f"[AudioRecorder] 保存原始音频到: {original_file}")

            sample_width = self.engine.get_sample_size()
            print(f"[AudioRecorder] 采样位宽: {sample_width}")

            # 合并所有音频帧
            audio_data = b''.join(self.audio_frames)
            print(f"[AudioRecorder] 合并后数据大小: {len(audio_data)} bytes")

            with wave.open(original_file, 'wb') as wf:
                wf.setnchannels(self.engine.channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(self.engine.sample_rate)
                wf.writeframes(audio_data)

            # 音频增强
            if enhance:
                try:
                    enhanced_audio = enhance_audio_quality(
                        self.audio_frames,
                        self.engine.sample_rate
                    )

                    enhanced_file = os.path.join(temp_dir, f"ququ_recording_enhanced_{timestamp}.wav")
                    with wave.open(enhanced_file, 'wb') as wf:
                        wf.setnchannels(self.engine.channels)
                        wf.setsampwidth(sample_width)
                        wf.setframerate(self.engine.sample_rate)
                        enhanced_bytes = (enhanced_audio * 32767).astype(np.int16).tobytes()
                        wf.writeframes(enhanced_bytes)

                    self.current_audio_file = enhanced_file
                    print(f"[AudioRecorder] 增强音频已保存: {enhanced_file}")

                except Exception as e:
                    print(f"[AudioRecorder] 音频增强失败: {e}")
                    self.current_audio_file = original_file
            else:
                self.current_audio_file = original_file

            file_size = os.path.getsize(self.current_audio_file)
            self.update_status(f"音频已保存: {file_size} bytes, {duration:.1f}秒")

            return self.current_audio_file

        except Exception as e:
            print(f"[AudioRecorder] 保存音频文件失败: {e}")
            return None

    def get_current_file(self) -> Optional[str]:
        """获取当前录音文件路径"""
        return self.current_audio_file

    def get_recording_duration(self) -> float:
        """获取录音时长"""
        if self.is_recording:
            return time.time() - self.start_time
        return 0.0

    def update_status(self, message: str):
        """更新状态（触发回调）"""
        if self.on_status_update:
            self.on_status_update(message)

    def set_device(self, device_index: Optional[int]):
        """设置录音设备"""
        self.device_index = device_index
        # 不再通过状态更新回调显示设备信息，改为在右侧专门显示

    def get_device_name(self, device_index: Optional[int]) -> str:
        """获取设备真实名称"""
        if device_index is None or not self.engine:
            return "默认设备"

        try:
            devices = self.engine.list_input_devices()
            for device in devices:
                if device.index == device_index:
                    return device.name
            return f"设备 {device_index}"
        except Exception:
            return f"设备 {device_index}"