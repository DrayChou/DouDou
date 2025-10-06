#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话框模块

提供各种对话框组件（设置、帮助等）
"""

import flet as ft
from typing import Callable, Dict, Any


class SettingsDialog:
    """设置对话框 - 支持新的配置结构"""

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

        # 获取AI服务配置
        ai_services = settings.get("ai_services", {})
        default_config = ai_services.get("default", {})
        translation_config = ai_services.get("translation", {})

        # === 默认AI服务配置 ===
        self.default_api_key_field = ft.TextField(
            label="API Key",
            value=default_config.get("api_key", ""),
            password=True,
            can_reveal_password=True,
            width=500,
        )

        self.default_base_url_field = ft.TextField(
            label="Base URL",
            value=default_config.get("base_url", ""),
            width=500,
            hint_text="例如: https://api.openai.com/v1",
        )

        self.default_model_name_field = ft.TextField(
            label="模型名称",
            value=default_config.get("model_name", ""),
            width=500,
            hint_text="例如: gpt-3.5-turbo, qwen-turbo",
        )

        # === 翻译服务配置 ===
        self.enable_translation_field = ft.Checkbox(
            label="启用翻译功能",
            value=settings.get("enable_translation", False),
        )

        self.translation_target_language_field = ft.Dropdown(
            label="目标语言",
            value=translation_config.get("target_language", "en"),
            width=240,
            options=[
                ft.dropdown.Option("en", "英语"),
                ft.dropdown.Option("ja", "日语"),
                ft.dropdown.Option("ko", "韩语"),
                ft.dropdown.Option("fr", "法语"),
                ft.dropdown.Option("de", "德语"),
                ft.dropdown.Option("es", "西班牙语"),
                ft.dropdown.Option("ru", "俄语"),
            ],
        )

        self.use_translation_api_field = ft.Checkbox(
            label="使用独立翻译API配置",
            value=translation_config.get("api_key") != default_config.get("api_key") or
                 translation_config.get("base_url") != default_config.get("base_url") or
                 translation_config.get("model_name") != default_config.get("model_name"),
        )

        self.translation_api_key_field = ft.TextField(
            label="翻译 API Key (可选)",
            value=translation_config.get("api_key", ""),
            password=True,
            can_reveal_password=True,
            width=500,
            visible=self.use_translation_api_field.value,
        )

        self.translation_base_url_field = ft.TextField(
            label="翻译 Base URL (可选)",
            value=translation_config.get("base_url", ""),
            width=500,
            hint_text="留空则使用默认配置",
            visible=self.use_translation_api_field.value,
        )

        self.translation_model_name_field = ft.TextField(
            label="翻译模型 (可选)",
            value=translation_config.get("model_name", ""),
            width=500,
            hint_text="留空则使用默认模型",
            visible=self.use_translation_api_field.value,
        )

        # === 语音识别设置 ===
        self.language_field = ft.Dropdown(
            label="识别语言",
            value=settings.get("language", "zh"),
            width=240,
            options=[
                ft.dropdown.Option("zh", "中文"),
                ft.dropdown.Option("en", "英文"),
                ft.dropdown.Option("ja", "日文"),
                ft.dropdown.Option("ko", "韩文"),
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
            label="启用AI文本修正",
            value=settings.get("enable_ai_optimization", True),
        )

        # 绑定翻译API配置显示切换
        self.use_translation_api_field.on_change = self._on_translation_api_toggle

        # 创建选项卡内容
        self.ai_tab_content = ft.Column([
            ft.Text("默认AI服务配置", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            self.default_api_key_field,
            self.default_base_url_field,
            self.default_model_name_field,
        ], scroll=ft.ScrollMode.AUTO, spacing=10)

        self.translation_tab_content = ft.Column([
            ft.Text("翻译功能设置", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            self.enable_translation_field,
            ft.Container(height=10),
            ft.Text("目标语言设置", size=14, weight=ft.FontWeight.BOLD),
            self.translation_target_language_field,
            ft.Container(height=15),
            ft.Text("独立API配置 (可选)", size=14, weight=ft.FontWeight.BOLD),
            self.use_translation_api_field,
            ft.Container(height=5),
            self.translation_api_key_field,
            self.translation_base_url_field,
            self.translation_model_name_field,
        ], scroll=ft.ScrollMode.AUTO, spacing=10)

        self.voice_tab_content = ft.Column([
            ft.Text("语音识别设置", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            self.language_field,
            self.use_vad_field,
            self.use_punc_field,
            self.enable_ai_field,
        ], scroll=ft.ScrollMode.AUTO, spacing=10)

        # 创建选项卡
        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="AI服务",
                    content=self.ai_tab_content,
                ),
                ft.Tab(
                    text="翻译设置",
                    content=self.translation_tab_content,
                ),
                ft.Tab(
                    text="语音识别",
                    content=self.voice_tab_content,
                ),
            ],
            expand=1,
        )

        # 创建对话框
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("应用设置"),
            content=ft.Container(
                content=self.tabs,
                width=600,
                height=500,
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

    # 兼容 flet_app 的接口
    def open(self):
        self.show()

    def _on_cancel(self, e):
        """取消按钮处理"""
        self.page.close(self.dialog)

    def _on_save(self, e):
        """保存按钮处理"""
        # 收集AI服务配置
        ai_services = self.settings.get("ai_services", {})

        # 更新默认配置
        default_config = ai_services.get("default", {})
        default_config.update({
            "api_key": self.default_api_key_field.value,
            "base_url": self.default_base_url_field.value,
            "model_name": self.default_model_name_field.value,
        })
        ai_services["default"] = default_config

        # 更新翻译配置
        translation_config = ai_services.get("translation", {})

        if self.use_translation_api_field.value:
            # 使用独立翻译API配置
            translation_config.update({
                "api_key": self.translation_api_key_field.value or default_config.get("api_key"),
                "base_url": self.translation_base_url_field.value or default_config.get("base_url"),
                "model_name": self.translation_model_name_field.value or default_config.get("model_name"),
                "target_language": self.translation_target_language_field.value,
            })
        else:
            # 使用默认配置
            translation_config.update({
                "target_language": self.translation_target_language_field.value,
            })
            # 继承默认API配置（不覆盖）
            if "api_key" not in translation_config:
                translation_config["api_key"] = default_config.get("api_key")
            if "base_url" not in translation_config:
                translation_config["base_url"] = default_config.get("base_url")
            if "model_name" not in translation_config:
                translation_config["model_name"] = default_config.get("model_name")

        ai_services["translation"] = translation_config

        # 收集其他设置
        new_settings = {
            "ai_services": ai_services,
            "language": self.language_field.value,
            "use_vad": self.use_vad_field.value,
            "use_punc": self.use_punc_field.value,
            "enable_ai_optimization": self.enable_ai_field.value,
            "enable_translation": self.enable_translation_field.value,
            # 保留其他未修改的设置
            **{k: v for k, v in self.settings.items()
               if k not in ["ai_services", "language", "use_vad", "use_punc", "enable_ai_optimization", "enable_translation"]}
        }

        # 调用回调
        self.on_save_callback(new_settings)

        # 关闭对话框
        self.page.close(self.dialog)

    def _on_translation_api_toggle(self, e):
        """翻译API配置切换处理"""
        use_separate_api = self.use_translation_api_field.value

        # 更新翻译API字段的可见性
        self.translation_api_key_field.visible = use_separate_api
        self.translation_base_url_field.visible = use_separate_api
        self.translation_model_name_field.visible = use_separate_api

        # 更新页面
        self.page.update()


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
