#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 组件模块

提供可复用的 Flet UI 组件
"""

import flet as ft
from typing import Optional, Callable


class RecordButton:
    """录音按钮组件"""

    def __init__(self, on_click: Callable):
        """
        初始化录音按钮

        Args:
            on_click: 点击回调函数
        """
        self.on_click_callback = on_click
        self.is_recording = False
        self.parent_container = None
        self._create_button()

    def _create_button(self):
        """创建按钮控件"""
        self.button = ft.ElevatedButton(
            text="开始录音",
            icon=ft.Icons.MIC,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=3,
                side=ft.BorderSide(width=1, color=ft.Colors.BLUE_500),
            ),
            on_click=self._on_click_wrapper,
            width=180,
            height=40,
        )
        print(f"[DEBUG] RecordButton 创建 - 文本: {self.button.text}, 图标: {self.button.icon}")

    def _on_click_wrapper(self, e):
        """点击事件包装器"""
        self.on_click_callback(e)

    def set_recording_state(self, is_recording: bool):
        """设置录音状态 - 通过重新创建按钮来确保图标更新"""
        print(f"[DEBUG] set_recording_state 被调用，状态: {is_recording}")
        self.is_recording = is_recording

        if is_recording:
            text = "停止录音"
            icon = ft.Icons.STOP
            style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=5,
                side=ft.BorderSide(width=2, color=ft.Colors.RED_500),
                bgcolor=ft.Colors.RED_500,
            )
        else:
            text = "开始录音"
            icon = ft.Icons.MIC
            style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=5,
                side=ft.BorderSide(width=2, color=ft.Colors.BLUE_500),
            )

        print(f"[DEBUG] 准备新按钮 - 文本: {text}, 图标: {icon}")

        # 重新创建按钮确保图标更新
        old_button = self.button
        self.button = ft.ElevatedButton(
            text=text,
            icon=icon,
            style=style,
            on_click=self._on_click_wrapper,
            width=180,
            height=40,
        )

        print(f"[DEBUG] 新按钮创建 - 文本: {self.button.text}, 图标: {self.button.icon}")

        # 如果有父容器，更新容器内容
        if self.parent_container:
            print(f"[DEBUG] 更新父容器内容")
            self.parent_container.content = self.button
            self.parent_container.update()

    def set_parent_container(self, container):
        """设置父容器引用"""
        self.parent_container = container

    def get_control(self) -> ft.Control:
        """获取Flet控件"""
        return self.button


class StatusDisplay:
    """状态显示组件"""

    def __init__(self):
        """初始化状态显示"""
        self.status_text = ft.Text(
            "准备就绪",
            size=14,
            color=ft.Colors.GREY_700,
        )

        self.progress_bar = ft.ProgressBar(
            value=0,
            width=260,
            bar_height=4,
            color=ft.Colors.BLUE_500,
            bgcolor=ft.Colors.BLUE_100,
        )

    def update_status(self, text: str, color: Optional[str] = None):
        """更新状态文本"""
        self.status_text.value = text
        if color:
            self.status_text.color = color

    def update_progress(self, value: float):
        """更新进度条"""
        self.progress_bar.value = min(max(value, 0), 1)

    def get_controls(self):
        """获取控件列表"""
        return [self.status_text, self.progress_bar]


class AudioVisualization:
    """音频可视化组件"""

    def __init__(self):
        """初始化音频可视化"""
        self.status_label = ft.Text("🔇 待机", size=11, color=ft.Colors.GREY_500)
        self.volume_bar = ft.ProgressBar(
            value=0,
            width=240,
            bar_height=6,
            color=ft.Colors.GREEN_500,
            bgcolor=ft.Colors.GREEN_100,
        )

        self.container = ft.Container(
            width=260,
            height=50,
            bgcolor=ft.Colors.BLACK12,
            border_radius=6,
            padding=6,
            content=ft.Column([
                ft.Row([self.status_label], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=3),
                self.volume_bar,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def update(self, status_text: str, volume_level: float = 0.0, color: str = ft.Colors.GREY_500):
        """
        更新可视化

        Args:
            status_text: 状态文本
            volume_level: 音量级别 (0-1)
            color: 文本颜色
        """
        self.status_label.value = status_text
        self.status_label.color = color
        self.volume_bar.value = min(volume_level, 1.0)

    def get_control(self) -> ft.Control:
        """获取Flet控件"""
        return self.container

    def set_recording(self, is_recording: bool):
        """设置录音状态"""
        if is_recording:
            self.update("🎤 正在录音", 0.0, ft.Colors.RED_500)
        else:
            self.update("🔇 待机", 0.0, ft.Colors.GREY_500)


# Import the new ResultCard implementation
from .result_card_new import ResultCard, ResultRecord


class ActionButtons:
    """操作按钮组"""

    def __init__(self, on_copy: Callable, on_export: Callable, on_clear: Callable, on_optimize: Callable):
        """
        初始化操作按钮组

        Args:
            on_copy: 复制按钮回调
            on_export: 导出按钮回调
            on_clear: 清空按钮回调
            on_optimize: AI优化按钮回调
        """
        self.copy_button = ft.ElevatedButton(
            text="复制",
            icon=ft.Icons.COPY,
            on_click=on_copy,
            disabled=True,
            width=75,
            height=30,
            style=ft.ButtonStyle(text_style=ft.TextStyle(size=12)),
        )

        self.export_button = ft.ElevatedButton(
            text="导出",
            icon=ft.Icons.SAVE_ALT,
            on_click=on_export,
            disabled=True,
            width=75,
            height=30,
            style=ft.ButtonStyle(text_style=ft.TextStyle(size=12)),
        )

        self.clear_button = ft.ElevatedButton(
            text="清空",
            icon=ft.Icons.CLEAR,
            on_click=on_clear,
            disabled=True,
            width=75,
            height=30,
            style=ft.ButtonStyle(text_style=ft.TextStyle(size=12)),
        )

        self.optimize_button = ft.ElevatedButton(
            text="AI汇总",
            icon=ft.Icons.SUMMARIZE,
            on_click=on_optimize,
            disabled=True,
            width=85,
            height=30,
            style=ft.ButtonStyle(text_style=ft.TextStyle(size=12)),
        )

        self.row = ft.Row(
            [self.copy_button, self.export_button, self.clear_button, self.optimize_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        )

    def enable_result_buttons(self, enabled: bool):
        """启用/禁用结果相关按钮"""
        self.copy_button.disabled = not enabled
        self.export_button.disabled = not enabled
        self.clear_button.disabled = not enabled
        self.optimize_button.disabled = not enabled

    def get_control(self) -> ft.Control:
        """获取Flet控件"""
        return self.row


class AudioDeviceSelector:
    """音频设备选择器组件"""

    def __init__(self, audio_engine, on_device_change: Callable):
        """
        初始化设备选择器

        Args:
            audio_engine: 音频引擎
            on_device_change: 设备变更回调
        """
        self.audio_engine = audio_engine
        self.dropdown = ft.Dropdown(
            label="录音设备",
            width=220,
            options=[],
            text_size=12,
            label_style=ft.TextStyle(size=12),
            on_change=lambda e: on_device_change(int(e.data) if e.data else None),
        )

        self.control = self.dropdown

        # 初始化设备列表
        self._refresh_devices()

    def _refresh_devices(self):
        """刷新设备列表"""
        if self.audio_engine:
            devices = self.audio_engine.list_input_devices()
            self.set_devices(devices)

    def set_devices(self, devices: list):
        """设置设备列表"""
        self.dropdown.options = [
            ft.dropdown.Option(key=str(d.index), text=d.name)
            for d in devices
        ]

    def set_selected_device(self, device_index: int):
        """设置选中的设备"""
        self.dropdown.value = str(device_index)

    def get_control(self) -> ft.Control:
        """获取Flet控件"""
        return self.control


class RealtimeModeToggle:
    """实时模式切换组件"""

    def __init__(self, on_change: Callable):
        """
        初始化实时模式切换

        Args:
            on_change: 模式变更回调
        """
        self.is_realtime = False
        self.on_change_callback = on_change
        self.switch = ft.Switch(
            label="实时模式",
            value=False,
            on_change=lambda e: self._handle_toggle(e),
        )

    def _handle_toggle(self, e):
        """处理切换事件"""
        self.is_realtime = e.data == "true" if isinstance(e.data, str) else e.data
        self.on_change_callback(self.is_realtime)

    def set_realtime(self, enabled: bool):
        """设置实时模式状态"""
        self.is_realtime = enabled
        self.switch.value = enabled
        if self.switch.page:
            self.switch.update()

    def get_control(self) -> ft.Control:
        """获取Flet控件"""
        return self.switch