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


class ResultCard:
    """结果显示卡片"""

    def __init__(self):
        """初始化结果卡片"""
        self.results_list = ft.ListView(
            spacing=8,
            expand=True,
            auto_scroll=True,
        )

        self.empty_text = ft.Text(
            "点击录音按钮开始...",
            size=13,
            color=ft.Colors.GREY_600,
            selectable=True,
        )

        self.card = ft.Card(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.TEXT_FORMAT, color=ft.Colors.BLUE_500, size=16),
                                ft.Text(
                                    "识别结果",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Divider(height=8),
                        self.results_list,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            elevation=2,
            width=None,  # 设置为None实现自适应宽度
            expand=True,
        )

        # 初始显示空状态
        self._show_empty_state()

    def _show_empty_state(self):
        """显示空状态"""
        self.results_list.controls = [
            ft.Container(
                content=self.empty_text,
                alignment=ft.alignment.center
            )
        ]
        self.empty_text.value = "点击录音按钮开始..."

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def add_result(self, text: str, color: Optional[str] = None):
        """添加新的识别结果"""
        # 如果是第一个结果，清除空状态
        if len(self.results_list.controls) == 1 and hasattr(self.results_list.controls[0].content, 'value') and self.results_list.controls[0].content.value == "点击录音按钮开始...":
            self.results_list.controls.clear()

        timestamp = self._get_timestamp()

        # 创建结果容器
        result_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        timestamp,
                        size=11,
                        color=ft.Colors.GREY_500,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(expand=True),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=4),
                ft.Text(
                    text,
                    size=13,
                    color=color or ft.Colors.BLACK87,
                    selectable=True,
                    width=None,  # 文本宽度自适应
                ),
            ]),
            padding=ft.padding.all(12),
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200),
            width=None,  # 容器宽度自适应
        )

        self.results_list.controls.append(result_container)

        # 强制滚动到底部
        if self.results_list.page:
            self.results_list.scroll_to(offset=-1, duration=300)

    def set_text(self, text: str, color: Optional[str] = None):
        """设置结果文本（兼容方法）"""
        if not text or text == "点击录音按钮开始...":
            self.clear_result()
        else:
            self.add_result(text, color)

    def set_result(self, text: str, color: Optional[str] = None):
        """设置结果文本（兼容方法）"""
        self.set_text(text, color)

    def get_result(self) -> str:
        """获取最后的结果文本"""
        if self.results_list.controls:
            # 找到最后一个文本内容
            for control in reversed(self.results_list.controls):
                if isinstance(control.content, ft.Column) and len(control.content.controls) >= 2:
                    text_control = control.content.controls[1]
                    if isinstance(text_control, ft.Text):
                        return text_control.value or ""
        return ""

    def get_recent_results(self, count: int = 3) -> list:
        """获取最近N条结果文本列表"""
        results = []
        for control in reversed(self.results_list.controls):
            if len(results) >= count:
                break
            if isinstance(control.content, ft.Column) and len(control.content.controls) >= 2:
                text_control = control.content.controls[1]
                if isinstance(text_control, ft.Text) and text_control.value:
                    results.append(text_control.value)
        return list(reversed(results))  # 返回正序（旧→新）

    def clear_result(self):
        """清空结果"""
        self.results_list.controls.clear()
        self._show_empty_state()

    def get_control(self) -> ft.Control:
        """获取Flet控件"""
        return self.card


class ActionButtons:
    """操作按钮组"""

    def __init__(self, on_copy: Callable, on_clear: Callable, on_settings: Callable):
        """
        初始化操作按钮组

        Args:
            on_copy: 复制按钮回调
            on_clear: 清空按钮回调
            on_settings: 设置按钮回调
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

        self.clear_button = ft.ElevatedButton(
            text="清空",
            icon=ft.Icons.CLEAR,
            on_click=on_clear,
            disabled=True,
            width=75,
            height=30,
            style=ft.ButtonStyle(text_style=ft.TextStyle(size=12)),
        )

        self.settings_button = ft.ElevatedButton(
            text="设置",
            icon=ft.Icons.SETTINGS,
            on_click=on_settings,
            width=75,
            height=30,
            style=ft.ButtonStyle(text_style=ft.TextStyle(size=12)),
        )

        self.row = ft.Row(
            [self.copy_button, self.clear_button, self.settings_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        )

    def enable_result_buttons(self, enabled: bool):
        """启用/禁用结果相关按钮"""
        self.copy_button.disabled = not enabled
        self.clear_button.disabled = not enabled

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