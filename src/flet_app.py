#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蛐蛐 (QuQu) - Flet 原型应用
基于 Flet 的现代化语音转文字应用
"""

import os
import flet as ft
from typing import Optional

from core import (
    AudioEngine,
    AudioRecorder,
    TranscriptionHandler,
    RecognitionPipeline,
    AIProcessor,
    HybridVADSegmenter,
    VADConfig,
    create_chinese_optimized_config,
)
from utils.config_manager import ConfigManager
from ui.dialogs import SettingsDialog, HelpDialog
from ui.components import (
    RecordButton,
    StatusDisplay,
    AudioVisualization,
    ResultCard,
    AudioDeviceSelector,
    RealtimeModeToggle,
)


class QuQuFletApp:
    """蛐蛐Flet应用主类 - 协调器模式"""

    def __init__(self, page: ft.Page):
        self.page = page
        self._setup_page()
        self._init_services()
        self._setup_ui()
        self._setup_callbacks()

    def _setup_page(self):
        """设置页面基本属性"""
        self.page.title = "蛐蛐 (QuQu) - 智能语音助手"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # 窗口设置
        self.page.window.width = 900
        self.page.window.height = 600
        self.page.window.min_width = 800
        self.page.window.min_height = 500
        self.page.window.resizable = True

        # 设置图标
        icon_ico_path = "assets/icon.ico"
        icon_png_path = "assets/icon.png"
        if os.path.exists(icon_ico_path):
            self.page.window.icon = icon_ico_path
        elif os.path.exists(icon_png_path):
            self.page.window.icon = icon_png_path

    def _init_services(self):
        """初始化核心服务"""
        # 配置管理
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.get_all()

        # 音频引擎
        try:
            self.audio_engine = AudioEngine(sample_rate=16000, chunk_size=1024, channels=1)
            self.audio_engine.initialise()
            print("[INFO] 音频引擎初始化成功")
        except Exception as e:
            print(f"[ERROR] 音频引擎初始化失败: {e}")
            self.audio_engine = None
            self.audio_disabled_mode = True

        # 录音管理器
        self.audio_recorder = AudioRecorder(self.audio_engine)

        # 识别流水线 - 使用直接集成模式
        self.recognition_pipeline = RecognitionPipeline(use_direct_integration=True)

        # AI处理器
        self.ai_processor = None
        if self.settings.get("enable_ai_optimization", False):
            self.ai_processor = AIProcessor(
                api_key=self.settings.get("api_key", ""),
                base_url=self.settings.get("base_url", ""),
                model_name=self.settings.get("model_name", "")
            )

        # 转写处理器
        self.transcription_handler = TranscriptionHandler(
            recognition_pipeline=self.recognition_pipeline,
            ai_processor=self.ai_processor
        )

        # VAD分段器 - 使用中文语音优化配置
        self.vad_config = create_chinese_optimized_config()
        self.vad_segmenter = HybridVADSegmenter(sample_rate=16000, config=self.vad_config)

    def _setup_ui(self):
        """设置UI界面"""
        # 顶部标题
        self.header = ft.Column(
            [
                ft.Text(
                    "🎤 蛐蛐 (QuQu)",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700,
                ),
                ft.Text(
                    "开源免费的智能语音助手",
                    size=14,
                    color=ft.Colors.GREY_600,
                ),
                ft.Divider(height=15),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 录音控制区域 - 用容器包装以便更新
        record_button_container = ft.Container()
        self.record_button = RecordButton(on_click=self.toggle_recording)
        self.record_button.set_parent_container(record_button_container)
        record_button_container.content = self.record_button.button

        self.status_display = StatusDisplay()

        self.audio_visualization = AudioVisualization()

        self.audio_device_selector = AudioDeviceSelector(
            audio_engine=self.audio_engine,
            on_device_change=self.on_audio_device_change
        )

        # 实时模式切换
        self.realtime_toggle = RealtimeModeToggle(
            on_change=self.toggle_realtime_mode
        )

        # 结果显示区域
        self.result_card = ResultCard()

        # 设备状态显示
        self.device_status_text = ft.Text(
            "音频设备: 默认设备",
            size=12,
            color=ft.Colors.GREY_600,
            italic=True,
        )

        # 设置按钮
        self.settings_button = ft.ElevatedButton(
            text="设置",
            icon=ft.Icons.SETTINGS,
            on_click=self.open_settings,
            width=85,
            height=32,
        )

        self.help_button = ft.ElevatedButton(
            text="帮助",
            icon=ft.Icons.HELP,
            on_click=self.open_help,
            width=85,
            height=32,
        )

        # 主界面布局
        self.main_layout = self._build_main_layout()
        self.page.add(self.main_layout)

        # 初始化设备状态显示（必须在UI创建之后）
        self.update_device_status(None)

    def _build_main_layout(self) -> ft.Control:
        """构建主界面布局"""
        # 左侧控制面板
        left_panel = ft.Container(
            width=300,
            padding=ft.padding.all(15),
            content=ft.Column([
                self.header,
                ft.Container(height=15),
                # 录音控制区域 - 录音按钮
                record_button_container,
                ft.Container(height=8),
                # 实时模式切换 - 放在录音按钮下方
                ft.Row([
                    ft.Container(width=15),  # 左边距
                    self.realtime_toggle.switch,
                    ft.Container(width=15),  # 右边距
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=12),
                self.status_display.status_text,
                ft.Container(height=12),
                self.audio_visualization.container,
                ft.Container(height=15),
                self.audio_device_selector.control,
                ft.Container(height=15),
                ft.Row([
                    self.settings_button,
                    ft.Container(width=8),
                    self.help_button,
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )

        # 右侧结果面板
        right_panel = ft.Container(
            expand=True,
            padding=ft.padding.all(15),
            content=ft.Column([
                # 设备信息区域
                ft.Container(
                    content=ft.Row([
                        self.device_status_text,
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=ft.padding.only(bottom=10),
                ),
                # 识别结果区域（占满剩余空间）
                ft.Container(
                    expand=True,
                    content=self.result_card.card
                ),
            ]),
        )

        return ft.Row([
            left_panel,
            ft.VerticalDivider(width=1),
            right_panel,
        ], expand=True)

    def _setup_callbacks(self):
        """设置回调函数"""
        # 录音回调
        self.audio_recorder.on_recording_started = self.on_recording_started
        self.audio_recorder.on_recording_stopped = self.on_recording_stopped
        self.audio_recorder.on_audio_level_update = self.update_audio_level
        self.audio_recorder.on_status_update = self.update_status

        # 转写回调
        self.transcription_handler.on_transcription_complete = self.on_transcription_complete
        self.transcription_handler.on_status_update = self.update_status
        self.transcription_handler.on_ai_optimization_complete = self.on_ai_optimization_complete

        # VAD回调
        self.vad_segmenter.on_segment_detected = self.on_vad_segment_detected

    # 录音控制
    def toggle_recording(self, e=None):
        """切换录音状态"""
        if not self.audio_engine:
            self.update_status("音频引擎未初始化，请检查音频设备")
            return

        if self.audio_recorder.is_recording:
            self.audio_recorder.stop_recording()
        else:
            from core.audio_engine import AudioStreamConfig
            stream_config = AudioStreamConfig(
                format=self.audio_engine.audio_format,
                channels=self.audio_engine.channels,
                rate=self.audio_engine.sample_rate,
                chunk=self.audio_engine.chunk_size,
                device_index=self.audio_recorder.device_index
            )
            self.audio_recorder.start_recording(stream_config)

    def on_recording_started(self):
        """录音开始回调"""
        self.record_button.set_recording_state(True)
        self.audio_visualization.set_recording(True)
        self.update_status("正在录音...")
        self.page.update()

    def on_recording_stopped(self, audio_file: str):
        """录音停止回调"""
        print(f"[DEBUG] 录音停止回调触发，音频文件: {audio_file}")
        self.record_button.set_recording_state(False)
        self.audio_visualization.set_recording(False)
        self.update_status("录音完成")
        self.page.update()

        # 开始转写
        if audio_file:
            print(f"[DEBUG] 开始转写音频文件: {audio_file}")
            self.transcription_handler.transcribe_audio_file(
                audio_file,
                enable_ai_optimization=self.settings.get("enable_ai_optimization", False)
            )
        else:
            print(f"[DEBUG] 没有音频文件，跳过转写")

    def update_audio_level(self, level: float):
        """更新音频级别显示"""
        self.audio_visualization.update("🎤 正在录音", level)

    def update_status(self, message: str):
        """更新状态显示"""
        self.status_display.update_status(message)
        self.page.update()

    # 转写处理
    def on_transcription_complete(self, result: dict):
        """转写完成回调"""
        print(f"[DEBUG] 转写完成回调触发，结果: {result}")
        if result.get("success"):
            text = result.get("text", "")
            print(f"[DEBUG] 转写成功，文本: {text[:100]}...")
            self.result_card.set_text(text)
            self.update_status("转写完成")
        else:
            error = result.get("error", "转写失败")
            print(f"[DEBUG] 转写失败，错误: {error}")
            self.update_status(f"转写失败: {error}")
        self.page.update()

    def on_ai_optimization_complete(self, optimized_text: str):
        """AI优化完成回调"""
        self.result_card.set_text(optimized_text)

    # 设备管理
    def on_audio_device_change(self, device_index: Optional[int]):
        """音频设备变更回调"""
        self.audio_recorder.set_device(device_index)
        # 更新设备状态显示
        self.update_device_status(device_index)

    def update_device_status(self, device_index: Optional[int]):
        """更新设备状态显示"""
        try:
            if device_index is None:
                device_name = "默认设备"
            else:
                device_name = self.audio_recorder.get_device_name(device_index)

            self.device_status_text.value = f"音频设备: {device_name}"
            self.page.update()
        except Exception as e:
            print(f"[DEBUG] 更新设备状态失败: {e}")
            self.device_status_text.value = "音频设备: 未知设备"
            self.page.update()

    # 实时模式
    def toggle_realtime_mode(self, is_realtime: bool):
        """切换实时模式"""
        self.update_status(f"实时模式: {'开启' if is_realtime else '关闭'}")

    def on_vad_segment_detected(self, segment):
        """VAD段落检测回调"""
        if self.realtime_toggle.is_realtime:
            self.update_status("检测到语音，正在处理...")

    # 结果操作
    def copy_result(self, e=None):
        """复制结果"""
        text = self.result_card.get_result()
        if text:
            self.page.set_clipboard(text)
            self.update_status("已复制到剪贴板")

    def optimize_text(self, e=None):
        """AI优化文本"""
        if self.ai_processor:
            text = self.result_card.get_result()
            if text:
                self.transcription_handler.optimize_text_async(text)

    def clear_result(self, e=None):
        """清空结果"""
        self.result_card.clear_result()
        self.transcription_handler.clear_result()

    # 对话框
    def open_settings(self, e=None):
        """打开设置对话框"""
        dialog = SettingsDialog(
            page=self.page,
            settings=self.settings,
            on_save=self.on_settings_changed
        )
        dialog.show()

    def open_help(self, e=None):
        """打开帮助对话框"""
        dialog = HelpDialog(page=self.page)
        dialog.show()

    def on_settings_changed(self, new_settings: dict):
        """设置变更回调"""
        self.settings = new_settings

        # 重新初始化AI处理器
        if new_settings.get("enable_ai_optimization", False):
            self.ai_processor = AIProcessor(
                api_key=new_settings.get("api_key", ""),
                base_url=new_settings.get("base_url", ""),
                model_name=new_settings.get("model_name", "")
            )
            self.transcription_handler.ai_processor = self.ai_processor
        else:
            self.ai_processor = None
            self.transcription_handler.ai_processor = None

        self.update_status("设置已更新")


def main():
    """主函数"""
    ft.app(target=QuQuFletApp, assets_dir="assets")


if __name__ == "__main__":
    main()