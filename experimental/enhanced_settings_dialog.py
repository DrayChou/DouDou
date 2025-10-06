#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强设置对话框模块

支持翻译配置和自定义Prompt编辑的设置界面
"""

import flet as ft
from typing import Callable, Dict, Any, Optional


class EnhancedSettingsDialog:
    """增强设置对话框"""

    def __init__(self, page: ft.Page, config_manager, on_save: Callable):
        """
        初始化增强设置对话框

        Args:
            page: Flet页面对象
            config_manager: 配置管理器实例
            on_save: 保存回调函数
        """
        self.page = page
        self.config_manager = config_manager
        self.on_save_callback = on_save
        self.settings = config_manager.get_all()

        # 创建输入字段
        self._create_basic_fields()
        self._create_translation_fields()
        self._create_prompt_fields()

        # 当前显示的Prompt编辑器
        self.current_prompt_editor: Optional[ft.TextField] = None
        self.current_prompt_type: str = ""

        # 创建对话框
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("应用设置", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                controls=[
                    ft.Tabs(
                        selected_index=0,
                        tabs=[
                            ft.Tab(
                                text="基础设置",
                                content=ft.Container(
                                    content=self._build_basic_settings_tab(),
                                    padding=ft.padding.all(20)
                                )
                            ),
                            ft.Tab(
                                text="翻译设置",
                                content=ft.Container(
                                    content=self._build_translation_settings_tab(),
                                    padding=ft.padding.all(20)
                                )
                            ),
                            ft.Tab(
                                text="Prompt配置",
                                content=ft.Container(
                                    content=self._build_prompt_settings_tab(),
                                    padding=ft.padding.all(20)
                                )
                            ),
                        ],
                        expand=1
                    )
                ],
                width=600,
                height=550,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            actions=[
                ft.TextButton("取消", on_click=self._on_cancel),
                ft.TextButton("保存", on_click=self._on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _create_basic_fields(self):
        """创建基础设置字段"""
        # AI服务配置
        ai_config = self.config_manager.get_ai_service_config("default")

        self.api_key_field = ft.TextField(
            label="API Key",
            value=ai_config.get("api_key", ""),
            password=True,
            can_reveal_password=True,
            width=520,
        )

        self.base_url_field = ft.TextField(
            label="Base URL",
            value=ai_config.get("base_url", ""),
            width=520,
            hint_text="例如: https://api.openai.com/v1",
        )

        self.model_name_field = ft.TextField(
            label="模型名称",
            value=ai_config.get("model_name", ""),
            width=520,
            hint_text="例如: gpt-3.5-turbo, qwen-turbo",
        )

        self.language_field = ft.Dropdown(
            label="识别语言",
            value=self.settings.get("language", "zh"),
            width=260,
            options=[
                ft.dropdown.Option("zh", "中文"),
                ft.dropdown.Option("en", "英文"),
            ],
        )

        self.use_vad_field = ft.Checkbox(
            label="使用语音活动检测(VAD)",
            value=self.settings.get("use_vad", True),
        )

        self.use_punc_field = ft.Checkbox(
            label="使用标点符号恢复",
            value=self.settings.get("use_punc", True),
        )

        self.enable_ai_field = ft.Checkbox(
            label="启用AI文本修正",
            value=self.settings.get("enable_ai_optimization", True),
        )

    def _create_translation_fields(self):
        """创建翻译设置字段"""
        self.enable_translation_field = ft.Checkbox(
            label="启用翻译功能",
            value=self.settings.get("enable_translation", False),
            on_change=self._on_translation_toggle,
        )

        translation_config = self.config_manager.get_ai_service_config("translation")

        self.translation_use_separate_field = ft.Checkbox(
            label="翻译使用独立配置（不勾选则复用AI修正配置）",
            value=translation_config.get("api_key") != "" or
                   translation_config.get("base_url") != "" or
                   translation_config.get("model_name") != "",
            on_change=self._on_separate_config_toggle,
        )

        self.translation_api_key_field = ft.TextField(
            label="翻译API Key",
            value=translation_config.get("api_key", ""),
            password=True,
            can_reveal_password=True,
            width=520,
            visible=False,
        )

        self.translation_base_url_field = ft.TextField(
            label="翻译Base URL",
            value=translation_config.get("base_url", ""),
            width=520,
            visible=False,
            hint_text="例如: https://api.openai.com/v1",
        )

        self.translation_model_name_field = ft.TextField(
            label="翻译模型名称",
            value=translation_config.get("model_name", ""),
            width=520,
            visible=False,
            hint_text="例如: gpt-3.5-turbo, qwen-turbo",
        )

        self.target_language_field = ft.Dropdown(
            label="目标语言",
            value=translation_config.get("target_language", "en"),
            width=260,
            options=[
                ft.dropdown.Option("en", "英文"),
                ft.dropdown.Option("ja", "日文"),
                ft.dropdown.Option("ko", "韩文"),
                ft.dropdown.Option("fr", "法文"),
                ft.dropdown.Option("de", "德文"),
                ft.dropdown.Option("es", "西班牙文"),
                ft.dropdown.Option("ru", "俄文"),
                ft.dropdown.Option("it", "意大利文"),
                ft.dropdown.Option("pt", "葡萄牙文"),
            ],
        )

    def _create_prompt_fields(self):
        """创建Prompt配置字段"""
        self.prompt_type_dropdown = ft.Dropdown(
            label="选择Prompt类型",
            value="correction",
            width=300,
            options=[
                ft.dropdown.Option("correction", "AI文本修正"),
                ft.dropdown.Option("translation", "文本翻译"),
            ],
            on_change=self._on_prompt_type_change,
        )

        self.prompt_editor = ft.TextField(
            label="Prompt内容",
            value=self.config_manager.load_prompt("correction"),
            multiline=True,
            min_lines=8,
            max_lines=15,
            width=520,
            expand=True,
        )

        self.use_prompt_file_field = ft.Checkbox(
            label="保存到文件（推荐长Prompt使用）",
            value=False,
            on_change=self._on_prompt_file_toggle,
        )

        self.reset_prompt_button = ft.ElevatedButton(
            "重置为默认",
            icon=ft.Icons.REFRESH,
            on_click=self._on_reset_prompt,
        )

    def _build_basic_settings_tab(self) -> ft.Column:
        """构建基础设置标签页"""
        return ft.Column(
            controls=[
                ft.Text("AI服务配置", size=16, weight=ft.FontWeight.BOLD),
                self.api_key_field,
                self.base_url_field,
                self.model_name_field,
                ft.Divider(height=20),
                ft.Text("语音识别设置", size=16, weight=ft.FontWeight.BOLD),
                self.language_field,
                ft.Row(
                    controls=[
                        self.use_vad_field,
                        self.use_punc_field,
                    ],
                    spacing=20
                ),
                ft.Divider(height=20),
                ft.Text("AI功能设置", size=16, weight=ft.FontWeight.BOLD),
                self.enable_ai_field,
            ],
            spacing=10,
            scroll=ft.ScrollMode.ADAPTIVE,
        )

    def _build_translation_settings_tab(self) -> ft.Column:
        """构建翻译设置标签页"""
        return ft.Column(
            controls=[
                ft.Text("翻译功能配置", size=16, weight=ft.FontWeight.BOLD),
                self.enable_translation_field,
                ft.Divider(height=15),
                ft.Text("目标语言", size=14, weight=ft.FontWeight.BOLD),
                self.target_language_field,
                ft.Divider(height=15),
                self.translation_use_separate_field,
                ft.Text("独立AI配置", size=14, weight=ft.FontWeight.BOLD),
                self.translation_api_key_field,
                self.translation_base_url_field,
                self.translation_model_name_field,
                ft.Container(
                    content=ft.Text(
                        "注意：如果不使用独立配置，翻译将复用AI修正的API设置",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                    margin=ft.margin.only(top=10)
                )
            ],
            spacing=10,
            scroll=ft.ScrollMode.ADAPTIVE,
        )

    def _build_prompt_settings_tab(self) -> ft.Column:
        """构建Prompt配置标签页"""
        return ft.Column(
            controls=[
                ft.Text("自定义Prompt配置", size=16, weight=ft.FontWeight.BOLD),
                self.prompt_type_dropdown,
                ft.Row(
                    controls=[
                        self.reset_prompt_button,
                        self.use_prompt_file_field,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(height=15),
                self.prompt_editor,
                ft.Container(
                    content=ft.Text(
                        "提示：长Prompt建议保存到文件，避免配置文件过大",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                    margin=ft.margin.only(top=10)
                )
            ],
            spacing=10,
            scroll=ft.ScrollMode.ADAPTIVE,
        )

    def _on_translation_toggle(self, e):
        """翻译功能开关切换"""
        pass

    def _on_separate_config_toggle(self, e):
        """独立配置开关切换"""
        visible = self.translation_use_separate_field.value
        self.translation_api_key_field.visible = visible
        self.translation_base_url_field.visible = visible
        self.translation_model_name_field.visible = visible
        self.page.update()

    def _on_prompt_type_change(self, e):
        """Prompt类型切换"""
        if self.current_prompt_editor:
            # 保存当前编辑的Prompt
            current_type = self.prompt_type_dropdown.value
            if current_type != self.current_prompt_type:
                # 这里可以添加自动保存逻辑
                pass

        # 加载新类型的Prompt
        prompt_type = self.prompt_type_dropdown.value
        self.prompt_editor.value = self.config_manager.load_prompt(prompt_type)
        self.current_prompt_type = prompt_type
        self.page.update()

    def _on_prompt_file_toggle(self, e):
        """Prompt文件保存方式切换"""
        pass

    def _on_reset_prompt(self, e):
        """重置Prompt为默认值"""
        prompt_type = self.prompt_type_dropdown.value

        if prompt_type == "correction":
            default_prompt = """你是语音识别文本修正专家，请优化以下语音识别文本：

要求：
1. 修正明显的语音识别错误
2. 添加适当的标点符号
3. 保持原意不变
4. 使表达更加流畅自然
5. 如果原文已经很好，可以不做修改

请直接返回优化后的文本，不要添加任何解释："""
        elif prompt_type == "translation":
            default_prompt = """你是专业翻译助手，请将以下文本翻译成目标语言：

要求：
1. 保持原意不变
2. 语法正确，表达自然
3. 符合目标语言的表达习惯
4. 专业术语翻译准确
5. 保留适当的格式和标点

请直接返回翻译后的文本，不要添加任何解释："""
        else:
            return

        self.prompt_editor.value = default_prompt
        self.page.update()

    def _on_cancel(self, e):
        """取消按钮点击"""
        self.dialog.open = False
        self.page.update()

    def _on_save(self, e):
        """保存按钮点击"""
        try:
            # 更新基础设置
            new_settings = {
                "language": self.language_field.value,
                "use_vad": self.use_vad_field.value,
                "use_punc": self.use_punc_field.value,
                "enable_ai_optimization": self.enable_ai_field.value,
                "enable_translation": self.enable_translation_field.value,
            }

            # 更新AI服务配置
            ai_services_config = {
                "default": {
                    "api_key": self.api_key_field.value,
                    "base_url": self.base_url_field.value,
                    "model_name": self.model_name_field.value,
                }
            }

            # 更新翻译配置
            translation_config = {
                "target_language": self.target_language_field.value,
            }

            if self.translation_use_separate_field.value:
                translation_config.update({
                    "api_key": self.translation_api_key_field.value,
                    "base_url": self.translation_base_url_field.value,
                    "model_name": self.translation_model_name_field.value,
                })

            ai_services_config["translation"] = translation_config

            # 更新完整配置
            new_settings["ai_services"] = ai_services_config

            # 保存Prompt
            prompt_type = self.prompt_type_dropdown.value
            prompt_content = self.prompt_editor.value
            use_file = self.use_prompt_file_field.value
            self.config_manager.save_prompt(prompt_type, prompt_content, use_file)

            # 保存配置
            for key, value in new_settings.items():
                self.config_manager.set(key, value)

            self.config_manager.save()

            # 调用回调
            if self.on_save_callback:
                self.on_save_callback(self.config_manager.get_all())

            self.dialog.open = False
            self.page.update()

            # 显示成功消息
            self._show_snackbar("设置已保存", ft.Colors.GREEN)

        except Exception as ex:
            self._show_snackbar(f"保存失败: {str(ex)}", ft.Colors.RED)

    def _show_snackbar(self, message: str, color: str):
        """显示提示消息"""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
            duration=3000,
        )
        self.page.overlay.append(snackbar)
        self.page.update()
        snackbar.open = True
        self.page.update()

    def open(self):
        """打开对话框"""
        self.page.open(self.dialog)

    def close(self):
        """关闭对话框"""
        self.dialog.open = False
        self.page.update()