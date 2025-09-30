#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蛐蛐 (QuQu) - Flet 原型应用
基于 Flet 的现代化语音转文字应用
"""

import os
import sys
import json
import tempfile
import threading
import time
import wave
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List

from datetime import datetime

import flet as ft
import numpy as np

from core.audio_engine import (
    AUDIO_BACKEND_NAME,
    AudioDeviceInfo,
    AudioEngine,
    AudioStreamConfig,
    AudioTestResult,
)
from core.vad_system import HybridVADSegmenter, VADConfig, VADSegment
from core.ai_integration import AIProcessor
from core.recognition_pipeline import RecognitionPipeline
from utils.config_manager import ConfigManager
from utils.audio_utils import enhance_audio_quality, calculate_rms_level


# 音频录制默认参数
CHUNK = 1024
CHANNELS = 1
RATE = 16000


@dataclass
class PendingSegment:
    """待处理的实时识别段"""

    audio_path: str
    info: Dict[str, Any]


class QuQuFletApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "蛐蛐 (QuQu) - 智能语音助手"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # 设置窗口为横版布局 - 2列设计
        self.page.window.width = 900  # 增加宽度适应2列布局
        self.page.window.height = 650  # 减少高度
        self.page.window.min_width = 800
        self.page.window.min_height = 550
        self.page.window.resizable = True

        # 设置应用图标 - 使用相对路径和ICO格式
        icon_ico_path = "assets/icon.ico"
        icon_png_path = "assets/icon.png"

        print(f"[DEBUG] 尝试设置ICO图标: {icon_ico_path}")
        if os.path.exists(icon_ico_path):
            self.page.window.icon = icon_ico_path
            print(f"[DEBUG] ICO图标设置成功: {icon_ico_path}")
        elif os.path.exists(icon_png_path):
            self.page.window.icon = icon_png_path
            print(f"[DEBUG] PNG图标设置成功: {icon_png_path}")
        else:
            print(f"[DEBUG] 图标文件不存在")

        # 状态变量
        self.is_recording = False
        self.audio_stream = None
        self.audio_frames: List[bytes] = []
        self.current_audio_file: Optional[str] = None
        self.transcription_result = ""
        self.funasr_process = None
        self.selected_audio_device: Optional[int] = None
        self.is_testing_audio = False
        self.working_audio_config: Optional[Dict[str, Any]] = None
        self.audio_disabled_mode = False

        # 核心服务组件
        self.audio_engine: Optional[AudioEngine] = None
        self.audio_format: Optional[int] = None
        try:
            self.audio_engine = AudioEngine(sample_rate=RATE, chunk_size=CHUNK, channels=CHANNELS)
            self.audio_backend_type = self.audio_engine.backend_name
        except RuntimeError as exc:
            self.audio_backend_type = AUDIO_BACKEND_NAME
            print(f"[ERROR] 初始化音频引擎失败: {exc}")

        self.config_manager = ConfigManager()
        self.settings = self.config_manager.get_all()
        self.recognition_pipeline = RecognitionPipeline()
        self.ai_processor: Optional[AIProcessor] = None

        # 实时语音识别相关状态
        self.is_realtime_mode = False
        self.realtime_thread = None
        self.vad_config = VADConfig()
        self.vad_segmenter = HybridVADSegmenter(sample_rate=RATE, config=self.vad_config)
        self.pending_recognition = False
        self.recognition_queue: List[PendingSegment] = []
        self.current_segment_text = ""

        # 创建UI组件
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 顶部标题栏
        self.header = ft.Column(
            [
                ft.Text(
                    "🎤 蛐蛐 (QuQu)",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700,
                ),
                ft.Text(
                    "开源免费的智能语音助手",
                    size=16,
                    color=ft.Colors.GREY_600,
                ),
                ft.Divider(height=20),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 录音控制区域
        self.record_button = ft.ElevatedButton(
            text="开始录音",
            icon=ft.Icons.MIC,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=5,
                side=ft.BorderSide(width=2, color=ft.Colors.BLUE_500),
            ),
            on_click=self.toggle_recording,
            width=200,  # 减小录音按钮宽度
            height=50,  # 稍微减小高度
        )

        self.status_text = ft.Text(
            "准备就绪",
            size=16,
            color=ft.Colors.GREY_700,
        )

        self.recording_progress = ft.ProgressBar(
            value=0,
            width=280,  # 减小组件宽度
            bar_height=6,  # 减小高度
            color=ft.Colors.BLUE_500,
            bgcolor=ft.Colors.BLUE_100,
        )

        # 统一的音频可视化组件 - 合并波形和音量显示
        self.audio_visualization = ft.Container(
            width=280,
            height=60,  # 统一高度容纳两行信息
            bgcolor=ft.Colors.BLACK12,
            border_radius=8,
            padding=8,
            content=ft.Column([
                # 顶部: 状态和波形
                ft.Row([
                    ft.Text("🔇 待机", size=12, color=ft.Colors.GREY_500),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=5),
                # 底部: 音量条
                ft.ProgressBar(
                    value=0,
                    width=260,
                    bar_height=8,
                    color=ft.Colors.GREEN_500,
                    bgcolor=ft.Colors.GREEN_100,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # 音频设备选择
        self.audio_device_dropdown = ft.Dropdown(
            label="录音设备",
            width=180,  # 减小下拉框宽度
            options=[],
            on_change=self.on_audio_device_change,
        )

        self.audio_test_button = ft.ElevatedButton(
            text="测试麦克风",
            icon=ft.Icons.HEARING,
            on_click=self.test_audio_device,
            width=100,  # 减小测试按钮宽度
        )

        # 设备选择区域 - 紧凑布局
        self.device_section = ft.Row(
            [
                self.audio_device_dropdown,
                ft.Container(width=5),  # 减小间距
                self.audio_test_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # 录音控制区域 - 紧凑布局，使用统一音频可视化
        self.recording_section = ft.Column(
            [
                # 设备选择
                self.device_section,
                ft.Container(height=10),  # 减小间距
                self.record_button,
                ft.Container(height=8),   # 减小间距
                self.status_text,
                ft.Container(height=8),   # 减小间距
                self.recording_progress,
                ft.Container(height=8),   # 减小间距
                # 统一音频可视化（包含波形和音量）
                ft.Text("音频监控", size=12, weight=ft.FontWeight.BOLD),
                self.audio_visualization,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 结果显示区域
        self.result_text = ft.Text(
            "点击录音按钮开始...",
            size=14,
            color=ft.Colors.GREY_600,
            selectable=True,
        )

        self.result_card = ft.Card(
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.TEXT_FORMAT, color=ft.Colors.BLUE_500),
                                ft.Text(
                                    "识别结果",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Divider(height=10),
                        self.result_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
            ),
            elevation=3,
            width=400,  # 减小结果卡片宽度
        )

        # 操作按钮区域 - 紧凑布局，防止文字换行
        self.action_buttons = ft.Row(
            [
                ft.ElevatedButton(
                    text="复制",
                    icon=ft.Icons.COPY,
                    on_click=self.copy_text,
                    disabled=True,
                    width=90,  # 增加宽度防止换行
                    height=35,
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(size=13),  # 稍小字体确保不换行
                    ),
                ),
                ft.ElevatedButton(
                    text="清空",
                    icon=ft.Icons.CLEAR,
                    on_click=self.clear_result,
                    disabled=True,
                    width=90,  # 增加宽度防止换行
                    height=35,
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(size=13),
                    ),
                ),
                ft.ElevatedButton(
                    text="设置",
                    icon=ft.Icons.SETTINGS,
                    on_click=self.open_settings,
                    width=90,  # 增加宽度防止换行
                    height=35,
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(size=13),
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,  # 稍微减小间距以容纳更宽的按钮
        )

        # 状态信息区域
        self.status_info = ft.Text(
            "系统就绪，准备录音",
            size=14,
            color=ft.Colors.GREY_600,
        )

        self.status_section = ft.Container(
            padding=15,  # 减小内边距
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_500),
                            ft.Text(
                                "状态信息",
                                size=14,  # 减小字体
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Divider(height=5),
                    self.status_info,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )

        # 添加所有组件到页面 - 2列布局设计，紧凑间距
        left_column = ft.Column(
            [
                self.header,
                ft.Container(height=15),  # 减小间距
                self.recording_section,
                ft.Container(height=15),  # 减小间距
                self.action_buttons,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        right_column = ft.Column(
            [
                ft.Container(height=30),  # 减小对齐高度
                self.result_card,
                ft.Container(height=15),  # 减小间距
                self.status_section,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        self.page.add(
            ft.Row(
                [
                    left_column,
                    ft.VerticalDivider(width=1),
                    right_column,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
                expand=True,
            )
        )

        # 加载配置
        self.load_settings_from_file()

        # 初始化音频系统
        self.init_audio_system()

    def update_audio_visualization(self, status_text: str, volume_level: float = 0.0, color: str = ft.Colors.GREY_500):
        """更新统一的音频可视化组件"""
        try:
            # 更新状态文本
            self.audio_visualization.content.controls[0].controls[0].value = status_text
            self.audio_visualization.content.controls[0].controls[0].color = color
            # 更新音量条
            self.audio_visualization.content.controls[2].value = min(volume_level, 1.0)
            self.page.update()
        except Exception as e:
            print(f"[DEBUG] 更新音频可视化失败: {e}")

    def init_audio_system(self):
        """初始化音频系统 - 增加详细诊断和自动测试"""
        try:
            if not self.audio_engine:
                raise RuntimeError("音频引擎不可用，请检查PyAudio依赖")

            self.audio_engine.initialise()
            self.audio_format = self.audio_engine.audio_format

            print(f"[DEBUG] 音频系统初始化成功，后端: {self.audio_engine.backend_name}")

            self.populate_audio_devices()
            self.auto_test_default_device()
            self.update_status("音频系统初始化成功")
        except Exception as e:
            print(f"[ERROR] 音频系统初始化失败: {str(e)}")
            self.update_status(f"音频系统初始化失败: {str(e)}")
            self.record_button.disabled = True
            self.page.update()

    def populate_audio_devices(self):
        """填充音频设备列表 - 增强 WASAPI 支持"""
        try:
            if not self.audio_engine:
                raise RuntimeError("音频引擎不可用")

            devices = self.audio_engine.list_input_devices()
            print(f"[DEBUG] 使用 {self.audio_engine.backend_name} 检测到 {len(devices)} 个音频设备")

            options: List[ft.dropdown.Option] = []
            wasapi_candidates: List[int] = []
            default_device: Optional[int] = None

            for device in devices:
                tags = []
                if device.is_wasapi:
                    tags.append("WASAPI")
                if device.is_loopback:
                    tags.append("Loopback")
                tag_suffix = f" [{' '.join(tags)}]" if tags else ""
                display_name = f"{device.name}{tag_suffix} {'(默认)' if device.is_default else ''}"

                options.append(ft.dropdown.Option(key=str(device.index), text=display_name))

                print(
                    f"[DEBUG]   [{device.index}] {device.name} - 输入通道: {device.max_input_channels}"
                    f"{tag_suffix} {'(默认)' if device.is_default else ''}"
                )

                if device.is_default:
                    default_device = device.index
                elif device.is_wasapi:
                    wasapi_candidates.append(device.index)

            chosen = default_device
            if chosen is None and wasapi_candidates:
                chosen = wasapi_candidates[0]
                print(f"[DEBUG] 优先选择 WASAPI 设备: {chosen}")
            if chosen is None and options:
                chosen = int(options[0].key)

            self.selected_audio_device = chosen
            self.audio_device_dropdown.options = options
            if chosen is not None:
                self.audio_device_dropdown.value = str(chosen)

            self.page.update()

            print(f"[DEBUG] 找到 {len(options)} 个可用输入设备")
        except Exception as e:
            print(f"[ERROR] 填充音频设备列表失败: {e}")

    def auto_test_default_device(self):
        """自动测试默认音频设备"""
        def auto_test_worker():
            """自动测试工作线程"""
            try:
                print("[DEBUG] 开始自动测试默认音频设备...")
                self.update_status("正在自动测试音频设备...")

                # 如果有选择的设备，先测试它
                if self.selected_audio_device is not None:
                    # 快速测试标准配置
                    success = self.test_pyaudio_standard()
                    if success:
                        self.update_status("✅ 默认设备测试成功，可以开始录音")
                        return

                # 如果没有成功，提示用户手动测试
                self.update_status("⚠️ 自动测试失败，请点击'测试麦克风'按钮")

            except Exception as e:
                print(f"[ERROR] 自动测试异常: {e}")
                self.update_status("⚠️ 自动测试异常，请手动测试音频设备")

        # 延迟1秒后启动自动测试，让UI有时间初始化
        import time
        def delayed_test():
            time.sleep(1)
            auto_test_worker()

        self.page.run_thread(delayed_test)

    def _build_stream_config(self, rate: int, chunk: int) -> AudioStreamConfig:
        if not self.audio_engine:
            raise RuntimeError("音频引擎不可用")
        fmt = self.audio_format or self.audio_engine.audio_format
        return AudioStreamConfig(
            format=fmt,
            channels=CHANNELS,
            rate=rate,
            chunk=chunk,
            device_index=self.selected_audio_device,
        )

    def _probe_audio_configs(self, configs: List[AudioStreamConfig], backend_label: str) -> bool:
        if not self.audio_engine:
            raise RuntimeError("音频引擎不可用")

        result = self.audio_engine.probe_stream(configs)
        if result.success and result.config:
            self.working_audio_config = result.config.to_dict()
            self.audio_backend_type = backend_label
            return True

        print(f"[DEBUG] {backend_label} 测试失败: {result.message}")
        return False

    def try_sounddevice_backend(self) -> bool:
        """尝试使用 sounddevice 作为音频后端"""
        try:
            print("[DEBUG] 尝试 sounddevice 后端...")
            import sounddevice as sd

            # 测试 sounddevice 是否可用
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]

            if len(input_devices) == 0:
                print("[DEBUG] sounddevice: 没有找到输入设备")
                return False

            print(f"[DEBUG] sounddevice 找到 {len(input_devices)} 个输入设备")

            # 测试录音
            duration = 0.1  # 0.1秒测试
            sample_rate = 16000

            recording = sd.rec(
                frames=int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype='int16'
            )
            sd.wait()

            if len(recording) > 0:
                # 保存 sounddevice 配置
                self.working_audio_config = {
                    "backend": "sounddevice",
                    "sample_rate": sample_rate,
                    "channels": 1,
                    "dtype": "int16"
                }
                self.audio_backend_type = "sounddevice"

                self.update_status("✅ sounddevice 后端测试成功！")
                print("[DEBUG] sounddevice 后端配置成功")
                return True

            return False

        except ImportError:
            print("[DEBUG] sounddevice 库未安装")
            self.update_status("💡 建议安装 sounddevice: pip install sounddevice")
            return False
        except Exception as e:
            print(f"[DEBUG] sounddevice 测试失败: {e}")
            return False

    def on_audio_device_change(self, e):
        """音频设备选择变更"""
        try:
            device_index = int(e.control.value)
            self.selected_audio_device = device_index
            if self.audio_engine:
                device_info = self.audio_engine.get_device_info_by_index(device_index)
                device_name = device_info.get('name', f'设备 {device_index}')
            else:
                device_name = f'设备 {device_index}'
            print(f"[DEBUG] 选择音频设备: [{device_index}] {device_name}")
            self.update_status(f"已选择设备: {device_name}")
        except Exception as e:
            print(f"[ERROR] 设备选择失败: {e}")

    def test_audio_device(self, e):
        """测试音频设备 - 增强版本"""
        if self.is_testing_audio or self.is_recording:
            return

        if self.selected_audio_device is None:
            self.update_status("请先选择音频设备")
            return

        self.is_testing_audio = True
        self.audio_test_button.text = "测试中..."
        self.audio_test_button.disabled = True
        self.page.update()

        def test_worker():
            """音频测试工作线程 - 多重后端尝试"""
            test_stream = None
            try:
                print(f"[DEBUG] 开始测试音频设备 {self.selected_audio_device}")

                # 方法1：PyAudioWPatch WASAPI配置（优先）
                if self.audio_engine and self.audio_engine.backend_name == "PyAudioWPatch":
                    success = self.test_pyaudiowpatch_wasapi()
                    if success:
                        return

                # 方法2：标准PyAudio配置
                success = self.test_pyaudio_standard()
                if success:
                    return

                # 方法3：Windows WASAPI模式
                success = self.test_pyaudio_wasapi()
                if success:
                    return

                # 方法3：DirectSound模式
                success = self.test_pyaudio_directsound()
                if success:
                    return

                # 方法4：系统默认设备强制测试
                success = self.test_system_default()
                if success:
                    return

                # 所有方法都失败
                self.update_status("❌ 所有音频后端测试失败，可能是驱动问题")
                self.working_audio_config = None
                self.audio_backend_type = "failed"

                # 尝试 sounddevice 作为最后的备用方案
                if self.try_sounddevice_backend():
                    return

                self.enable_audio_disabled_mode()
                print("[ERROR] 所有音频测试方法都失败了")

            except Exception as e:
                print(f"[ERROR] 音频设备测试异常: {e}")
                self.update_status(f"❌ 设备测试异常: {str(e)}")
            finally:
                self.is_testing_audio = False
                self.audio_test_button.text = "测试麦克风"
                self.audio_test_button.disabled = False
                # 重置音频可视化
                self.update_audio_visualization("🔇 待机", 0.0, ft.Colors.GREY_500)

        # 使用Flet线程启动测试
        self.page.run_thread(test_worker)

    def test_pyaudiowpatch_wasapi(self) -> bool:
        """测试 PyAudioWPatch WASAPI 配置"""
        try:
            configs = [
                self._build_stream_config(48_000, 1_024),
                self._build_stream_config(44_100, 2_048),
                self._build_stream_config(16_000, 512),
                self._build_stream_config(22_050, 1_024),
            ]
            success = self._probe_audio_configs(configs, "pyaudiowpatch_wasapi")
            if success and self.working_audio_config:
                rate = self.working_audio_config.get("rate", 0)
                self.update_status(f"✅ WASAPI 设备测试成功 ({rate}Hz)")
            return success
        except Exception as exc:
            print(f"[DEBUG] PyAudioWPatch WASAPI 测试异常: {exc}")
            return False

    def test_pyaudio_standard(self) -> bool:
        """测试标准PyAudio配置"""
        try:
            configs = [self._build_stream_config(RATE, CHUNK)]
            success = self._probe_audio_configs(configs, "standard")
            if success:
                self.update_status("✅ 标准模式测试成功！")
            return success
        except Exception as exc:
            print(f"[DEBUG] 标准PyAudio测试失败: {exc}")
            return False

    def test_pyaudio_wasapi(self) -> bool:
        """测试Windows WASAPI模式"""
        try:
            configs = [
                self._build_stream_config(44_100, 2_048),
                self._build_stream_config(48_000, 1_024),
                self._build_stream_config(16_000, 512),
            ]
            success = self._probe_audio_configs(configs, "wasapi")
            if success and self.working_audio_config:
                rate = self.working_audio_config.get("rate", 0)
                self.update_status(f"✅ WASAPI 模式测试成功 ({rate}Hz)")
            return success
        except Exception as exc:
            print(f"[DEBUG] WASAPI 测试失败: {exc}")
            return False

    def test_pyaudio_directsound(self) -> bool:
        """测试DirectSound模式"""
        try:
            configs = [self._build_stream_config(RATE, CHUNK)]
            success = self._probe_audio_configs(configs, "directsound")
            if success:
                self.update_status("✅ DirectSound 模式测试成功！")
            return success
        except Exception as exc:
            print(f"[DEBUG] DirectSound 测试失败: {exc}")
            return False

    def test_system_default(self) -> bool:
        """测试系统默认设备"""
        try:
            if not self.audio_engine:
                raise RuntimeError("音频引擎不可用")
            default_info = self.audio_engine.get_default_input_device_info()
            default_index = default_info.get('index')
            default_name = default_info.get('name', '默认设备')
            self.selected_audio_device = default_index
            if default_index is not None:
                self.audio_device_dropdown.value = str(default_index)
            configs = [self._build_stream_config(RATE, CHUNK)]
            success = self._probe_audio_configs(configs, "system_default")
            if success:
                self.update_status(f"✅ 系统默认设备测试成功: {default_name}")
            return success
        except Exception as exc:
            print(f"[DEBUG] 系统默认设备测试失败: {exc}")
            return False

    def toggle_recording(self, e):
        """切换录音状态"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始录音 - 使用经过测试的音频配置"""
        try:
            if not self.audio_engine:
                self.update_status("❌ 音频引擎不可用")
                return

            # 检查是否有经过测试的音频配置
            if not self.working_audio_config:
                self.update_status("⚠️ 请先测试音频设备")
                return

            if self.audio_backend_type == "failed":
                self.update_status("❌ 音频设备测试失败，无法录音")
                return

            self.is_recording = True
            self.audio_frames = []

            # 更新UI
            self.record_button.text = "停止录音"
            self.record_button.icon = ft.Icons.STOP
            self.record_button.style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=5,
                side=ft.BorderSide(width=2, color=ft.Colors.RED_500),
                bgcolor=ft.Colors.RED_500,
            )
            self.status_text.value = "正在录音..."
            self.status_text.color = ft.Colors.RED_700
            self.recording_progress.value = 0

            # 使用经过测试的音频配置
            config = self.working_audio_config
            print(f"[DEBUG] 使用{self.audio_backend_type}后端配置开始录音")
            print(f"[DEBUG] 配置: {config}")

            stream_config = AudioStreamConfig.from_dict(config)
            self.audio_stream = self.audio_engine.open_input_stream(stream_config)

            print(f"[DEBUG] 音频流已创建并启动，使用{self.audio_backend_type}后端")

            # 启动录音和进度线程
            self.start_recording_thread()
            self.start_progress_timer()

            self.update_status(f"录音开始 - 使用{self.audio_backend_type}后端")
            self.page.update()

        except Exception as e:
            print(f"[ERROR] 开始录音失败: {str(e)}")
            self.update_status(f"开始录音失败: {str(e)}")
            self.is_recording = False
            self.page.update()

    def verify_audio_device(self):
        """验证音频设备可用性 - 使用已测试的配置"""
        try:
            if not self.working_audio_config:
                print("[DEBUG] 没有可用的音频配置，需要先测试设备")
                return False

            if self.audio_backend_type == "failed":
                print("[DEBUG] 音频后端测试失败")
                return False

            print(f"[DEBUG] 验证音频设备成功，使用{self.audio_backend_type}后端")
            return True

        except Exception as e:
            print(f"[ERROR] 音频设备验证失败: {e}")
            self.update_status(f"音频设备不可用: {str(e)}")
            return False

    def stop_recording(self):
        """停止录音"""
        try:
            self.is_recording = False

            # 停止音频流
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None

            # 更新UI
            self.record_button.text = "开始录音"
            self.record_button.icon = ft.Icons.MIC
            self.record_button.style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=5,
                side=ft.BorderSide(width=2, color=ft.Colors.BLUE_500),
            )
            self.status_text.value = "处理中..."
            self.status_text.color = ft.Colors.ORANGE_700

            # 保存音频文件
            self.save_audio_file()

            self.update_status("录音停止，正在处理...")
            self.page.update()

            # 启动转录处理
            self.process_transcription()

        except Exception as e:
            self.update_status(f"停止录音失败: {str(e)}")
            self.page.update()

    def start_recording_thread(self):
        """启动录音线程 - 使用经过测试的配置"""
        def recording_worker():
            """录音工作线程 - 持续读取音频数据"""
            print(f"[DEBUG] 录音线程开始，使用{self.audio_backend_type}后端")
            frame_count = 0
            silent_frames = 0
            audio_levels = []

            # 获取当前的音频配置
            chunk_size = self.working_audio_config["chunk"]
            rate = self.working_audio_config["rate"]

            try:
                while self.is_recording and self.audio_stream:
                    try:
                        # 使用正确的块大小读取音频数据
                        data = self.audio_stream.read(chunk_size, exception_on_overflow=False)
                        if data and self.is_recording:
                            self.audio_frames.append(data)
                            frame_count += 1

                            # 分析音频电平
                            audio_data = np.frombuffer(data, dtype=np.int16)
                            rms_level = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                            max_level = np.max(np.abs(audio_data))
                            audio_levels.append(rms_level)

                            # 实时更新UI
                            if frame_count % 5 == 0:  # 每5帧更新一次UI，避免过于频繁
                                # 计算音量百分比
                                volume_percent = min(rms_level / 5000, 1.0)

                                # 更新统一音频可视化
                                if rms_level > 1000:
                                    waveform_text = f"🔊 录音中: {rms_level:.0f}"
                                    color = ft.Colors.GREEN_500
                                elif rms_level > 100:
                                    waveform_text = f"🔉 录音中: {rms_level:.0f}"
                                    color = ft.Colors.ORANGE_500
                                else:
                                    waveform_text = f"🔇 静音: {rms_level:.1f}"
                                    color = ft.Colors.RED_500

                                self.update_audio_visualization(waveform_text, volume_percent, color)

                            # 检测静音帧
                            if rms_level < 100:  # 非常低的音频电平
                                silent_frames += 1

                            # 每收集100帧打印一次调试信息
                            if frame_count % 100 == 0:
                                avg_rms = np.mean(audio_levels[-100:]) if audio_levels else 0
                                print(f"[DEBUG] 录音线程已收集 {frame_count} 帧，每帧 {len(data)} bytes")
                                print(f"[DEBUG] 音频电平 - RMS: {rms_level:.1f}, MAX: {max_level}, 平均RMS: {avg_rms:.1f}")
                                print(f"[DEBUG] 静音帧比例: {silent_frames/frame_count*100:.1f}%")

                    except Exception as e:
                        print(f"[WARNING] 读取音频数据时出错: {e}")
                        # 短暂延迟后继续
                        time.sleep(0.01)

            except Exception as e:
                print(f"[ERROR] 录音线程异常: {e}")
            finally:
                if audio_levels:
                    avg_rms = np.mean(audio_levels)
                    max_rms = np.max(audio_levels)
                    print(f"[DEBUG] 录音线程结束，总共收集了 {frame_count} 帧音频数据")
                    print(f"[DEBUG] 音频统计 - 平均RMS: {avg_rms:.1f}, 最大RMS: {max_rms:.1f}")
                    print(f"[DEBUG] 静音帧: {silent_frames}/{frame_count} ({silent_frames/frame_count*100:.1f}%)")

                    if avg_rms < 50:
                        print(f"[WARNING] 音频电平过低，可能录音设备有问题!")

        # 使用 Flet 的线程方法启动录音线程
        self.page.run_thread(recording_worker)

    def audio_callback(self, in_data, frame_count, time_info, status):
        """音频录制回调 - 已弃用，改用阻塞模式"""
        # 这个函数现在不再使用，保留以防需要回退
        pass

    def start_progress_timer(self):
        """启动进度计时器 - 显示录音时长，无时间限制"""
        def update_progress():
            """在后台线程中更新录音进度 - 持续录音模式"""
            start_time = time.time()
            while self.is_recording:
                elapsed = time.time() - start_time

                # 显示录音时长（无上限）
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)

                # 更新进度条显示录音时长
                # 使用脉冲模式表示持续录音
                progress_value = (elapsed % 2) / 2  # 2秒循环的脉冲效果
                self.recording_progress.value = progress_value

                # 更新状态文本显示录音时长
                self.status_text.value = f"正在录音... {minutes:02d}:{seconds:02d}"
                self.page.update()

                time.sleep(0.1)

        # 使用 Flet 0.28.3 官方线程方法启动进度更新
        self.page.run_thread(update_progress)

    def save_audio_file(self):
        """保存音频文件 - 增加音频预处理和增强"""
        try:
            print(f"[DEBUG] 开始保存音频文件，总帧数: {len(self.audio_frames)}")

            if not self.audio_frames:
                print("[ERROR] 没有音频数据可保存!")
                self.update_status("错误：没有录制到音频数据")
                return

            # 计算音频数据总大小
            total_bytes = sum(len(frame) for frame in self.audio_frames)
            duration_estimate = total_bytes / (RATE * 2)  # 16位=2字节
            print(f"[DEBUG] 音频数据总大小: {total_bytes} bytes, 预估时长: {duration_estimate:.2f}秒")

            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 保存原始音频作为备份
            original_file = os.path.join(temp_dir, f"ququ_recording_original_{timestamp}.wav")
            with wave.open(original_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                sample_width = self.audio_engine.get_sample_size() if self.audio_engine else 2
                wf.setsampwidth(sample_width)
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.audio_frames))

            # 尝试音频增强
            try:
                enhanced_audio_data = self.enhance_audio_quality(self.audio_frames)
                print(f"[DEBUG] 音频增强完成，处理了 {len(enhanced_audio_data)} 个样本")

                # 保存增强后的音频
                self.current_audio_file = os.path.join(temp_dir, f"ququ_recording_enhanced_{timestamp}.wav")
                with wave.open(self.current_audio_file, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    sample_width = self.audio_engine.get_sample_size() if self.audio_engine else 2
                    wf.setsampwidth(sample_width)
                    wf.setframerate(RATE)
                    # 将numpy数组转换回字节
                    enhanced_bytes = (enhanced_audio_data * 32767).astype(np.int16).tobytes()
                    wf.writeframes(enhanced_bytes)

                print(f"[DEBUG] 增强音频文件已保存: {self.current_audio_file}")

            except Exception as e:
                print(f"[WARNING] 音频增强失败，使用原始音频: {e}")
                self.current_audio_file = original_file

            # 检查保存的文件大小
            file_size = os.path.getsize(self.current_audio_file)
            print(f"[DEBUG] 最终音频文件: {self.current_audio_file}, 文件大小: {file_size} bytes")

            self.update_status(f"音频已保存: {file_size} bytes, 预估{duration_estimate:.1f}秒")

        except Exception as e:
            print(f"[ERROR] 保存音频文件失败: {str(e)}")
            self.update_status(f"保存音频文件失败: {str(e)}")

    def enhance_audio_quality(self, audio_frames):
        """音频质量增强 - 模拟WebAudio API的增强效果"""
        try:
            # 将音频帧转换为numpy数组
            audio_data = b''.join(audio_frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0

            print(f"[DEBUG] 开始音频增强，样本数: {len(audio_array)}")

            # 1. 噪音抑制 - 简单的低通滤波
            audio_array = self.apply_noise_suppression(audio_array)

            # 2. 自动增益控制 - 归一化音量
            audio_array = self.apply_auto_gain_control(audio_array)

            # 3. 动态范围压缩 - 提高语音清晰度
            audio_array = self.apply_dynamic_range_compression(audio_array)

            return audio_array

        except Exception as e:
            print(f"[ERROR] 音频增强失败: {e}")
            # 如果增强失败，返回原始数据
            audio_data = b''.join(audio_frames)
            return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0

    def apply_noise_suppression(self, audio_array):
        """噪音抑制 - 修复滤波器参数"""
        try:
            from scipy import signal
            # 修复滤波器频率设置：语音频率范围 300-7000Hz
            nyquist = RATE * 0.5  # 8000Hz

            # 设计带通滤波器，保留语音频率范围
            low_freq = 300 / nyquist   # 0.0375
            high_freq = 7000 / nyquist  # 0.875

            # 确保频率在有效范围内 (0, 1)
            low_freq = max(0.01, min(0.99, low_freq))
            high_freq = max(0.01, min(0.99, high_freq))

            if low_freq >= high_freq:
                high_freq = 0.9
                low_freq = 0.1

            print(f"[DEBUG] 滤波器频率范围: {low_freq:.3f} - {high_freq:.3f}")

            # 使用带通滤波器而非低通滤波器
            b, a = signal.butter(4, [low_freq, high_freq], btype='band')
            filtered_audio = signal.lfilter(b, a, audio_array)
            print(f"[DEBUG] 噪音抑制完成")
            return filtered_audio
        except ImportError:
            print("[DEBUG] scipy不可用，跳过噪音抑制")
            return audio_array
        except Exception as e:
            print(f"[WARNING] 噪音抑制失败: {e}")
            return audio_array

    def apply_auto_gain_control(self, audio_array):
        """自动增益控制 - 优化增益参数"""
        try:
            # 计算RMS音量
            rms = np.sqrt(np.mean(audio_array ** 2))
            if rms > 0:
                # 降低目标RMS，避免过度放大
                target_rms = 0.05  # 降低目标音量
                gain = target_rms / rms
                # 更严格的增益限制
                gain = np.clip(gain, 0.3, 2.0)  # 限制增益范围0.3-2.0
                audio_array = audio_array * gain
                print(f"[DEBUG] 自动增益控制完成，增益: {gain:.2f}, RMS: {rms:.4f} -> {target_rms:.4f}")
            return audio_array
        except Exception as e:
            print(f"[WARNING] 自动增益控制失败: {e}")
            return audio_array

    def apply_dynamic_range_compression(self, audio_array):
        """动态范围压缩 - 温和压缩参数"""
        try:
            # 更温和的压缩器设置
            threshold = 0.5  # 提高阈值
            ratio = 2.0      # 降低压缩比

            # 对超过阈值的部分进行温和压缩
            above_threshold = np.abs(audio_array) > threshold
            sign = np.sign(audio_array)
            abs_audio = np.abs(audio_array)

            # 压缩公式：output = threshold + (input - threshold) / ratio
            compressed = np.where(above_threshold,
                                sign * (threshold + (abs_audio - threshold) / ratio),
                                audio_array)

            # 检查压缩效果
            compressed_count = np.sum(above_threshold)
            print(f"[DEBUG] 动态范围压缩完成，压缩了 {compressed_count} 个样本")
            return compressed
        except Exception as e:
            print(f"[WARNING] 动态范围压缩失败: {e}")
            return audio_array

    def process_transcription(self):
        """处理转录 - 使用 Flet 0.28.3 推荐的线程安全方法"""
        if not self.current_audio_file:
            print("[ERROR] 没有可处理的音频文件")
            self.update_status("没有可处理的音频文件")
            return

        print(f"[DEBUG] 开始处理转录，音频文件: {self.current_audio_file}")

        # 使用 Flet 官方推荐的 page.run_thread() 方法启动后台任务
        # 这是 Flet 0.28.3 版本的正确线程安全实现方式
        def transcribe_in_background():
            """在后台线程中执行转录任务"""
            try:
                print(f"[DEBUG] 转录线程开始，处理文件: {self.current_audio_file}")

                # 使用FunASR服务器进行转录
                result = self.transcribe_with_funasr(self.current_audio_file)

                print(f"[DEBUG] FunASR转录结果: {result}")

                # 更新转录结果 - 在后台线程中直接调用，Flet会处理线程安全
                self.update_transcription_result(result)

            except Exception as e:
                error_msg = f"转录失败: {str(e)}"
                print(f"[ERROR] 转录异常: {e}")
                # 更新错误状态 - 在后台线程中直接调用，Flet会处理线程安全
                self.update_status(error_msg)

        # 使用 Flet 0.28.3 的官方线程方法 - 自动处理线程安全
        self.page.run_thread(transcribe_in_background)

    def transcribe_with_funasr(self, audio_file: str) -> Dict[str, Any]:
        """使用FunASR进行转录 - 修复版本"""
        try:
            # 检查FunASR服务器脚本
            funasr_script = os.path.join(os.path.dirname(__file__), "funasr_server.py")

            if not os.path.exists(funasr_script):
                return {
                    "success": False,
                    "error": "FunASR服务器脚本不存在",
                    "text": "FunASR服务器脚本不存在"
                }

            # 准备命令输入 - 修复 JSON 换行符问题
            input_data = {
                "action": "transcribe",
                "audio_path": audio_file,
                "options": {
                    "use_vad": True,
                    "use_punc": True,
                    "language": "zh"
                }
            }

            # 修复：使用正确的输入格式，添加换行符让服务器知道命令结束
            input_text = json.dumps(input_data, ensure_ascii=False) + '\n'

            # 运行FunASR服务器进行转录 - 修复超时和缓冲问题
            process = subprocess.Popen(
                [sys.executable, funasr_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0  # 无缓冲模式
            )

            try:
                # 发送命令并获取响应 - 增加超时时间
                stdout, stderr = process.communicate(input=input_text, timeout=120)

                if process.returncode == 0:
                    # 解析第一行的初始化结果，第二行的转录结果
                    lines = stdout.strip().split('\n')
                    if len(lines) >= 2:
                        # 尝试解析转录结果（通常是最后一行）
                        try:
                            result_line = lines[-1]
                            output = json.loads(result_line)

                            if output.get("success"):
                                return {
                                    "success": True,
                                    "text": output.get("text", ""),
                                    "confidence": output.get("confidence", 0.0),
                                    "duration": output.get("duration", 0.0)
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": output.get("error", "转录失败"),
                                    "text": f"转录失败: {output.get('error', '未知错误')}"
                                }
                        except json.JSONDecodeError as je:
                            return {
                                "success": False,
                                "error": f"解析转录结果失败: {str(je)}",
                                "text": f"解析失败，原始输出: {stdout[:200]}..."
                            }
                    else:
                        return {
                            "success": False,
                            "error": "服务器响应格式错误",
                            "text": f"响应行数不足: {len(lines)}, 内容: {stdout[:200]}..."
                        }
                else:
                    return {
                        "success": False,
                        "error": f"服务器执行失败 (代码: {process.returncode})",
                        "text": f"错误信息: {stderr[:200]}..."
                    }

            finally:
                # 确保进程被正确关闭
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "转录超时",
                "text": "转录超时，请稍后重试"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": f"转录异常: {str(e)}"
            }

    def update_transcription_result(self, result: Dict[str, Any]):
        """更新转录结果 - 增加AI优化流程"""
        if result.get("success"):
            raw_text = result.get("text", "")
            self.transcription_result = raw_text

            # 立即显示原始识别结果
            self.result_text.value = raw_text
            self.status_text.value = "识别完成"
            self.status_text.color = ft.Colors.BLUE_700

            # 启用操作按钮
            self.action_buttons.controls[0].disabled = False  # 复制按钮
            self.action_buttons.controls[1].disabled = False  # 清空按钮

            # 显示置信度
            confidence = result.get("confidence", 0.0)
            duration = result.get("duration", 0.0)
            self.update_status(f"识别完成 - 置信度: {confidence:.2f}, 时长: {duration:.2f}秒")

            self.page.update()

            # 异步启动AI优化处理
            if self.settings.get("enable_ai_optimization", True) and raw_text.strip():
                self.start_ai_optimization(raw_text, result)
            else:
                print("[DEBUG] AI优化已禁用或文本为空，跳过优化")

        else:
            self.result_text.value = result.get("text", "转录失败")
            self.status_text.value = "转录失败"
            self.status_text.color = ft.Colors.RED_700
            self.update_status(f"转录失败: {result.get('error', '未知错误')}")
            self.page.update()

    def start_ai_optimization(self, raw_text: str, original_result: Dict[str, Any]):
        """启动AI文本优化处理"""
        def ai_optimization_worker():
            """AI优化工作线程"""
            try:
                print(f"[DEBUG] 开始AI文本优化: {raw_text[:50]}...")

                # 更新状态显示正在优化
                self.status_text.value = "AI正在优化文本..."
                self.status_text.color = ft.Colors.ORANGE_700
                self.page.update()

                # 调用AI优化
                optimized_result = self.optimize_text_with_ai(raw_text)

                if optimized_result.get("success"):
                    optimized_text = optimized_result.get("text", "").strip()

                    if optimized_text and optimized_text != raw_text.strip():
                        # AI优化成功且有改进
                        self.transcription_result = optimized_text
                        self.result_text.value = optimized_text
                        self.status_text.value = "AI优化完成"
                        self.status_text.color = ft.Colors.GREEN_700

                        print(f"[DEBUG] AI优化成功: {optimized_text[:50]}...")
                        self.update_status(f"AI优化完成 - 原文本已改进")
                    else:
                        # AI未改进文本
                        print(f"[DEBUG] AI优化无改进，保持原文本")
                        self.status_text.value = "识别完成"
                        self.status_text.color = ft.Colors.BLUE_700
                        self.update_status(f"文本无需优化")
                else:
                    # AI优化失败
                    error_msg = optimized_result.get("error", "优化失败")
                    print(f"[WARNING] AI优化失败: {error_msg}")
                    self.update_status(f"AI优化失败: {error_msg}")

                self.page.update()

            except Exception as e:
                print(f"[ERROR] AI优化异常: {e}")
                self.update_status(f"AI优化异常: {str(e)}")
                self.page.update()

        # 使用Flet线程启动AI优化
        self.page.run_thread(ai_optimization_worker)

    def optimize_text_with_ai(self, text: str) -> Dict[str, Any]:
        """使用AI优化文本"""
        try:
            # 检查AI配置
            api_key = self.settings.get("api_key", "").strip()
            base_url = self.settings.get("base_url", "").strip()
            model_name = self.settings.get("model_name", "").strip()

            if not all([api_key, base_url, model_name]):
                return {
                    "success": False,
                    "error": "AI配置不完整，请在设置中配置API Key、Base URL和模型名称"
                }

            # 构建优化提示词
            optimization_prompt = f"""请优化以下语音识别文本，修正可能的识别错误，补充标点符号，使其更符合中文表达习惯：

原文：{text}

优化要求：
1. 修正明显的语音识别错误
2. 添加适当的标点符号
3. 保持原意不变
4. 使表达更加流畅自然
5. 如果原文已经很好，可以不做修改

请直接返回优化后的文本，不要添加任何解释："""

            # 调用AI API（这里需要根据具体的AI服务实现）
            optimized_text = self.call_ai_api(optimization_prompt, api_key, base_url, model_name)

            if optimized_text:
                return {
                    "success": True,
                    "text": optimized_text.strip()
                }
            else:
                return {
                    "success": False,
                    "error": "AI返回空结果"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def call_ai_api(self, prompt: str, api_key: str, base_url: str, model_name: str) -> str:
        """调用AI API进行文本优化"""
        try:
            import requests
            import json

            # 构建API请求
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }

            # 确保base_url格式正确
            if not base_url.endswith('/'):
                base_url += '/'
            if not base_url.endswith('chat/completions'):
                base_url += 'chat/completions'

            print(f"[DEBUG] 调用AI API: {base_url}")

            # 发送请求
            response = requests.post(
                base_url,
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    optimized_text = result['choices'][0]['message']['content'].strip()
                    print(f"[DEBUG] AI优化成功")
                    return optimized_text
                else:
                    print(f"[ERROR] AI API响应格式错误: {result}")
                    return ""
            else:
                print(f"[ERROR] AI API请求失败: {response.status_code}, {response.text}")
                return ""

        except Exception as e:
            print(f"[ERROR] AI API调用异常: {e}")
            return ""

    def copy_text(self, e):
        """复制文本到剪贴板"""
        if self.transcription_result:
            self.page.set_clipboard(self.transcription_result)
            self.update_status("文本已复制到剪贴板")
            self.page.update()

    def clear_result(self, e):
        """清空结果"""
        self.transcription_result = ""
        self.result_text.value = "点击录音按钮开始..."
        self.status_text.value = "准备就绪"
        self.status_text.color = ft.Colors.GREY_700

        # 禁用操作按钮
        self.action_buttons.controls[0].disabled = True
        self.action_buttons.controls[1].disabled = True

        self.update_status("结果已清空")
        self.page.update()

    def update_status(self, message: str):
        """更新状态信息"""
        self.status_info.value = f"{datetime.now().strftime('%H:%M:%S')} - {message}"
        self.page.update()

    def open_settings(self, e):
        """打开设置对话框"""
        # 创建配置输入字段
        api_key_field = ft.TextField(
            label="API Key",
            value=self.settings["api_key"],
            password=True,
            can_reveal_password=True,
            width=480,  # 400 * 1.2 = 480
        )

        base_url_field = ft.TextField(
            label="Base URL",
            value=self.settings["base_url"],
            width=480,  # 400 * 1.2 = 480
            hint_text="例如: https://api.openai.com/v1",
        )

        model_name_field = ft.TextField(
            label="模型名称",
            value=self.settings["model_name"],
            width=480,  # 400 * 1.2 = 480
            hint_text="例如: gpt-3.5-turbo, qwen-turbo",
        )

        language_field = ft.Dropdown(
            label="语言",
            value=self.settings["language"],
            width=240,  # 200 * 1.2 = 240
            options=[
                ft.dropdown.Option("zh", "中文"),
                ft.dropdown.Option("en", "英文"),
            ],
        )

        use_vad_field = ft.Checkbox(
            label="使用语音活动检测(VAD)",
            value=self.settings["use_vad"],
        )

        use_punc_field = ft.Checkbox(
            label="使用标点符号恢复",
            value=self.settings["use_punc"],
        )

        enable_ai_field = ft.Checkbox(
            label="启用AI文本优化",
            value=self.settings["enable_ai_optimization"],
        )

        def save_settings(e):
            self.settings["api_key"] = api_key_field.value
            self.settings["base_url"] = base_url_field.value
            self.settings["model_name"] = model_name_field.value
            self.settings["language"] = language_field.value
            self.settings["use_vad"] = use_vad_field.value
            self.settings["use_punc"] = use_punc_field.value
            self.settings["enable_ai_optimization"] = enable_ai_field.value

            # 保存配置到文件
            self.save_settings_to_file()

            self.page.close(dlg)
            self.update_status("设置已保存")

        def test_connection(e):
            # 这里可以添加测试连接的功能
            self.update_status("测试连接功能待实现")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("应用设置"),
            content=ft.Column(
                [
                    ft.Text("AI服务配置", size=18, weight=ft.FontWeight.BOLD),
                    api_key_field,
                    base_url_field,
                    model_name_field,
                    ft.Divider(height=20),
                    ft.Text("语音识别设置", size=18, weight=ft.FontWeight.BOLD),
                    language_field,
                    use_vad_field,
                    use_punc_field,
                    enable_ai_field,
                ],
                width=540,  # 450 * 1.2 = 540
                height=400,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            actions=[
                ft.TextButton("测试连接", on_click=test_connection),
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("保存", on_click=save_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dlg)

    def show_audio_help_dialog(self):
        """显示音频问题帮助对话框"""
        def close_help(e):
            self.page.close(help_dlg)

        def open_admin_guide(e):
            self.page.close(help_dlg)
            self.show_admin_guide_dialog()

        help_content = ft.Column([
            ft.Text("🎤 音频设备问题诊断", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
            ft.Divider(height=10),

            ft.Text("检测到音频驱动兼容性问题：", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("• 错误代码: [Errno -9999] Unanticipated host error", color=ft.Colors.RED_600),
            ft.Text("• 这是Windows音频驱动的常见问题", color=ft.Colors.GREY_700),

            ft.Divider(height=15),
            ft.Text("🔧 立即解决方案:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),

            ft.Container(
                content=ft.Column([
                    ft.Text("1. 以管理员身份运行 (推荐)", weight=ft.FontWeight.BOLD),
                    ft.Text("   • 关闭当前应用", color=ft.Colors.GREY_600),
                    ft.Text("   • 右键点击命令提示符 → 以管理员身份运行", color=ft.Colors.GREY_600),
                    ft.Text("   • 重新执行: python flet_app.py", color=ft.Colors.GREY_600),
                ]),
                padding=10,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=8,
            ),

            ft.Container(height=10),

            ft.Container(
                content=ft.Column([
                    ft.Text("2. 检查麦克风权限", weight=ft.FontWeight.BOLD),
                    ft.Text("   • 设置 → 隐私 → 麦克风", color=ft.Colors.GREY_600),
                    ft.Text("   • 确保'允许应用访问麦克风'已开启", color=ft.Colors.GREY_600),
                    ft.Text("   • 确保'允许桌面应用访问麦克风'已开启", color=ft.Colors.GREY_600),
                ]),
                padding=10,
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=8,
            ),

            ft.Container(height=10),

            ft.Container(
                content=ft.Column([
                    ft.Text("3. 其他解决方案", weight=ft.FontWeight.BOLD),
                    ft.Text("   • 更新音频驱动程序", color=ft.Colors.GREY_600),
                    ft.Text("   • 尝试使用USB麦克风", color=ft.Colors.GREY_600),
                    ft.Text("   • 重启计算机", color=ft.Colors.GREY_600),
                ]),
                padding=10,
                bgcolor=ft.Colors.GREEN_50,
                border_radius=8,
            )
        ], width=500, height=350, scroll=ft.ScrollMode.ADAPTIVE)  # 减小对话框尺寸

        help_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("音频问题帮助"),
            content=help_content,
            actions=[
                ft.TextButton("查看详细指南", on_click=open_admin_guide),
                ft.TextButton("我知道了", on_click=close_help),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(help_dlg)

    def show_admin_guide_dialog(self):
        """显示管理员权限详细指南"""
        def close_guide(e):
            self.page.close(guide_dlg)

        guide_content = ft.Column([
            ft.Text("🛡️ 以管理员身份运行指南", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
            ft.Divider(height=10),

            ft.Text("Windows 管理员权限可以解决大多数音频驱动问题。", size=14),

            ft.Divider(height=15),
            ft.Text("📋 详细步骤:", size=16, weight=ft.FontWeight.BOLD),

            ft.Container(
                content=ft.Column([
                    ft.Text("步骤 1: 关闭当前应用", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                    ft.Text("• 关闭这个蛐蛐应用窗口", color=ft.Colors.GREY_600),
                    ft.Text("• 关闭当前的命令提示符窗口", color=ft.Colors.GREY_600),
                ]),
                padding=10,
                bgcolor=ft.Colors.RED_50,
                border_radius=8,
            ),

            ft.Container(height=8),

            ft.Container(
                content=ft.Column([
                    ft.Text("步骤 2: 以管理员身份打开命令提示符", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                    ft.Text("• 按 Win+R 打开运行对话框", color=ft.Colors.GREY_600),
                    ft.Text("• 输入 'cmd' 然后按 Ctrl+Shift+Enter", color=ft.Colors.GREY_600),
                    ft.Text("• 或者: 搜索'命令提示符' → 右键 → 以管理员身份运行", color=ft.Colors.GREY_600),
                ]),
                padding=10,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=8,
            ),

            ft.Container(height=8),

            ft.Container(
                content=ft.Column([
                    ft.Text("步骤 3: 重新运行应用", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                    ft.Text("• 在管理员命令提示符中执行:", color=ft.Colors.GREY_600),
                    ft.Container(
                        content=ft.Text("cd D:\\Code\\ququ_flet",
                                      size=12,
                                      color=ft.Colors.WHITE,
                                      selectable=True),
                        padding=8,
                        bgcolor=ft.Colors.BLACK,
                        border_radius=4,
                    ),
                    ft.Container(
                        content=ft.Text("python flet_app.py",
                                      size=12,
                                      color=ft.Colors.WHITE,
                                      selectable=True),
                        padding=8,
                        bgcolor=ft.Colors.BLACK,
                        border_radius=4,
                    ),
                ]),
                padding=10,
                bgcolor=ft.Colors.GREEN_50,
                border_radius=8,
            ),

            ft.Container(height=10),
            ft.Text("💡 提示: 如果问题仍然存在，可能需要更新音频驱动或检查硬件连接。",
                   size=12, color=ft.Colors.ORANGE_700, weight=ft.FontWeight.BOLD),
        ], width=520, height=400, scroll=ft.ScrollMode.ADAPTIVE)  # 减小管理员指南对话框

        guide_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("管理员权限指南"),
            content=guide_content,
            actions=[
                ft.TextButton("明白了", on_click=close_guide),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(guide_dlg)

    def enable_audio_disabled_mode(self):
        """启用音频禁用模式"""
        self.audio_disabled_mode = True

        # 更新录音按钮
        self.record_button.text = "音频不可用"
        self.record_button.icon = ft.Icons.MIC_OFF
        self.record_button.disabled = True
        self.record_button.style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            elevation=2,
            side=ft.BorderSide(width=2, color=ft.Colors.GREY_400),
            bgcolor=ft.Colors.GREY_200,
        )

        # 更新状态文本
        self.status_text.value = "音频系统不可用"
        self.status_text.color = ft.Colors.GREY_600

        # 禁用音频相关按钮
        self.audio_test_button.disabled = True
        self.audio_device_dropdown.disabled = True

        # 更新结果显示为演示模式
        self.result_text.value = "🎤 音频系统暂时不可用\n\n📱 你可以体验以下功能：\n\n1. 查看现代化的界面设计\n2. 测试设置对话框\n3. 了解AI文本优化功能\n\n💡 解决音频问题后即可使用语音识别功能"

        # 启用部分操作按钮用于演示
        self.action_buttons.controls[2].disabled = False  # 设置按钮保持可用

        self.update_status("已启用演示模式 - 可体验界面和设置功能")
        self.page.update()

        # 延迟显示音频问题对话框，让UI先更新
        def show_help_delayed():
            import time
            time.sleep(1)  # 延迟1秒
            self.show_audio_help_dialog()

        self.page.run_thread(show_help_delayed)

    def save_settings_to_file(self):
        """保存配置到文件"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), "ququ_settings.json")
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")

    def load_settings_from_file(self):
        """从文件加载配置"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), "ququ_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
        except Exception as e:
            print(f"加载设置失败: {e}")

    def on_window_close(self, e):
        """窗口关闭事件处理"""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()

            if self.audio_engine:
                self.audio_engine.terminate()

            # 清理临时文件
            if self.current_audio_file and os.path.exists(self.current_audio_file):
                os.remove(self.current_audio_file)

        except Exception as e:
            print(f"清理资源时发生错误: {e}")

def main():
    """主函数"""
    # 设置Flet应用
    ft.app(target=QuQuFletApp, assets_dir="assets")

if __name__ == "__main__":
    main()
