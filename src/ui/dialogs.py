#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话框模块

提供各种对话框组件（设置、帮助等）
"""

import flet as ft
from typing import Callable, Dict, Any


class SettingsDialog:
    """设置对话框"""

    def __init__(self, page: ft.Page, settings: Dict[str, Any], on_save: Callable):
        """
        初始化设置对话框

        Args:
            page: Flet页面对象
            settings: 当前设置字典
            on_save: 保存回调函数
        """
        self.page = page
        self.settings = settings
        self.on_save_callback = on_save

        # 创建输入字段
        self.api_key_field = ft.TextField(
            label="API Key",
            value=settings.get("api_key", ""),
            password=True,
            can_reveal_password=True,
            width=480,
        )

        self.base_url_field = ft.TextField(
            label="Base URL",
            value=settings.get("base_url", ""),
            width=480,
            hint_text="例如: https://api.openai.com/v1",
        )

        self.model_name_field = ft.TextField(
            label="模型名称",
            value=settings.get("model_name", ""),
            width=480,
            hint_text="例如: gpt-3.5-turbo, qwen-turbo",
        )

        self.language_field = ft.Dropdown(
            label="语言",
            value=settings.get("language", "zh"),
            width=240,
            options=[
                ft.dropdown.Option("zh", "中文"),
                ft.dropdown.Option("en", "英文"),
            ],
        )

        self.use_vad_field = ft.Checkbox(
            label="使用语音活动检测(VAD)",
            value=settings.get("use_vad", True),
        )

        self.use_punc_field = ft.Checkbox(
            label="使用标点符号恢复",
            value=settings.get("use_punc", True),
        )

        self.enable_ai_field = ft.Checkbox(
            label="启用AI文本优化",
            value=settings.get("enable_ai_optimization", True),
        )

        # 创建对话框
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("应用设置"),
            content=ft.Column(
                [
                    ft.Text("AI服务配置", size=18, weight=ft.FontWeight.BOLD),
                    self.api_key_field,
                    self.base_url_field,
                    self.model_name_field,
                    ft.Divider(height=20),
                    ft.Text("语音识别设置", size=18, weight=ft.FontWeight.BOLD),
                    self.language_field,
                    self.use_vad_field,
                    self.use_punc_field,
                    self.enable_ai_field,
                ],
                width=540,
                height=400,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            actions=[
                ft.TextButton("取消", on_click=self._on_cancel),
                ft.TextButton("保存", on_click=self._on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def show(self):
        """显示对话框"""
        self.page.open(self.dialog)

    def _on_cancel(self, e):
        """取消按钮处理"""
        self.page.close(self.dialog)

    def _on_save(self, e):
        """保存按钮处理"""
        # 收集设置
        new_settings = {
            "api_key": self.api_key_field.value,
            "base_url": self.base_url_field.value,
            "model_name": self.model_name_field.value,
            "language": self.language_field.value,
            "use_vad": self.use_vad_field.value,
            "use_punc": self.use_punc_field.value,
            "enable_ai_optimization": self.enable_ai_field.value,
        }

        # 调用回调
        self.on_save_callback(new_settings)

        # 关闭对话框
        self.page.close(self.dialog)


class HelpDialog:
    """帮助对话框"""

    def __init__(self, page: ft.Page):
        """
        初始化帮助对话框

        Args:
            page: Flet页面对象
        """
        self.page = page

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
                    ft.Text("   • 重新执行: python main.py", color=ft.Colors.GREY_600),
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
                ]),
                padding=10,
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=8,
            ),
        ], width=500, height=350, scroll=ft.ScrollMode.ADAPTIVE)

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("音频问题帮助"),
            content=help_content,
            actions=[
                ft.TextButton("我知道了", on_click=self._on_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def show(self):
        """显示对话框"""
        self.page.open(self.dialog)

    def _on_close(self, e):
        """关闭按钮处理"""
        self.page.close(self.dialog)


def create_settings_dialog(page: ft.Page, config_manager, on_save: Callable):
    """
    创建设置对话框的工厂函数

    Args:
        page: Flet页面对象
        config_manager: 配置管理器实例
        on_save: 保存回调函数

    Returns:
        设置对话框实例
    """
    try:
        # 尝试导入增强设置对话框
        from .enhanced_settings_dialog import EnhancedSettingsDialog
        return EnhancedSettingsDialog(page, config_manager, on_save)
    except ImportError:
        # 如果导入失败，使用基础设置对话框
        print("[警告] 无法导入增强设置对话框，使用基础版本")
        settings = config_manager.get_all()
        return SettingsDialog(page, settings, on_save)