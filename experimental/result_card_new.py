#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果显示卡片模块（重新设计）

支持关联的识别、修正、翻译结果展示
"""

import flet as ft
from typing import Optional, Dict, Any
from datetime import datetime


class ResultRecord:
    """单个识别记录，包含原文、修正和翻译"""

    def __init__(self, original_text: str, record_id: str = None):
        self.original_text = original_text
        self.record_id = record_id or f"record_{int(datetime.now().timestamp() * 1000)}"
        self.optimized_text = None  # 修正后的文本
        self.translated_text = None  # 翻译后的文本
        self.target_language = None  # 翻译目标语言代码
        self.timestamp = datetime.now()
        self.controls = []  # 存储对应的UI控件，避免查找

    def add_correction(self, optimized_text: str):
        """添加修正结果"""
        self.optimized_text = optimized_text

    def add_translation(self, translated_text: str, target_language: Optional[str] = None):
        """添加翻译结果"""
        self.translated_text = translated_text
        if target_language:
            self.target_language = target_language

    def to_controls(self) -> list:
        """转换为Flet控件"""
        controls = []

        # 识别原文
        controls.append(ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        self.timestamp.strftime("%H:%M:%S"),
                        size=11,
                        color=ft.Colors.GREY_500,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(expand=True),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=4),
                ft.Text(
                    self.original_text,
                    size=13,
                    color=ft.Colors.BLACK87,
                    selectable=True,
                    width=None,
                ),
            ]),
            padding=ft.padding.all(12),
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200),
            width=None,
        ))

        # 修正结果
        if self.optimized_text:
            controls.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(
                            "[AI修正]",
                            size=11,
                            color=ft.Colors.ORANGE_700,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(expand=True),
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Container(height=2),
                    ft.Text(
                        self.optimized_text,
                        size=13,
                        color=ft.Colors.BLACK87,
                        selectable=True,
                        width=None,
                    ),
                ]),
                padding=ft.padding.only(left=20, right=12, top=8, bottom=8),
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=8,
                # Flet's border.only expects BorderSide objects per side
                border=ft.border.only(left=ft.BorderSide(width=4, color=ft.Colors.ORANGE_300)),
                width=None,
            ))

        # 翻译结果
        if self.translated_text:
            controls.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(
                            f"[翻译 → {self._get_target_language_name()}]",
                            size=11,
                            color=ft.Colors.GREEN_700,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(expand=True),
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Container(height=2),
                    ft.Text(
                        self.translated_text,
                        size=13,
                        color=ft.Colors.BLACK87,
                        selectable=True,
                        width=None,
                    ),
                ]),
                padding=ft.padding.only(left=20, right=12, top=8, bottom=8),
                bgcolor=ft.Colors.GREEN_50,
                border_radius=8,
                border=ft.border.only(left=ft.BorderSide(width=4, color=ft.Colors.GREEN_300)),
                width=None,
            ))

        return controls

    def _get_target_language_name(self) -> str:
        """获取目标语言名称"""
        # 这里可以从配置中获取，暂时硬编码一些常用语言
        language_names = {
            "en": "英文",
            "ja": "日文",
            "ko": "韩文",
            "fr": "法文",
            "de": "德文",
            "es": "西班牙文",
            "ru": "俄文",
            "it": "意大利文",
            "pt": "葡萄牙文",
        }
        # 优先使用记录的目标语言代码
        if self.target_language:
            return language_names.get(self.target_language, self.target_language)
        return "翻译"


class ResultCard:
    """结果显示卡片（重新设计）"""

    def __init__(self):
        """初始化结果卡片"""
        self.results_list = ft.Column(
            spacing=8,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
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
                content=ft.Column([
                    ft.Row([
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

        # 记录管理 - 每个识别记录包含原文、修正、翻译
        self.records = []  # 按时间顺序存储所有记录
        self.record_lookup = {}  # 通过record_id查找记录的字典

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
        return datetime.now().strftime("%H:%M:%S")

    def add_recognition_result(self, original_text: str, record_id: str = None) -> str:
        """添加新的识别结果"""
        # 如果是第一个结果，清除空状态
        if len(self.results_list.controls) == 1 and hasattr(self.results_list.controls[0].content, 'value') and self.results_list.controls[0].content.value == "点击录音按钮开始...":
            self.results_list.controls.clear()

        # 创建新的识别记录
        record = ResultRecord(original_text, record_id)
        self.records.append(record)
        self.record_lookup[record.record_id] = record

        # 将记录转换为控件并插入到顶部
        controls = record.to_controls()
        record.controls = controls  # 存储控件引用，优化后续查找
        for control in controls:
            self.results_list.controls.insert(0, control)

        # 刷新界面
        if self.results_list.page:
            self.results_list.scroll_to(offset=0, duration=200)

        return record.record_id

    def add_correction_result(self, record_id: str, optimized_text: str):
        """为指定记录添加修正结果"""
        record = self.record_lookup.get(record_id)
        if record:
            record.add_correction(optimized_text)
            self._refresh_record(record)

    def add_translation_result(self, record_id: str, translated_text: str, target_language: Optional[str] = None):
        """为指定记录添加翻译结果"""
        record = self.record_lookup.get(record_id)
        if record:
            record.add_translation(translated_text, target_language)
            self._refresh_record(record)

    def _refresh_record(self, record: ResultRecord):
        """刷新指定记录的显示（优化版本）"""
        if not record.controls:
            # 如果没有存储控件引用，回退到查找模式（兼容性）
            self._refresh_record_legacy(record)
            return

        # 找到第一个控件在列表中的位置
        try:
            first_control = record.controls[0]
            record_index = self.results_list.controls.index(first_control)
        except (IndexError, ValueError):
            # 控件不在列表中，可能已被删除
            return

        # 移除旧控件
        for control in record.controls:
            if control in self.results_list.controls:
                self.results_list.controls.remove(control)

        # 生成新控件
        new_controls = record.to_controls()
        record.controls = new_controls  # 更新引用

        # 在原位置插入新控件
        for i, control in enumerate(new_controls):
            self.results_list.controls.insert(record_index + i, control)

        # 刷新界面
        if self.results_list.page:
            self.results_list.update()

    def _refresh_record_legacy(self, record: ResultRecord):
        """旧的刷新方法（兼容性保留）"""
        # 找到这个记录在results_list中的位置
        record_index = None
        start_index = 0

        for i, control in enumerate(self.results_list.controls):
            if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                # 检查是否是识别文本容器
                for sub_control in control.content.controls:
                    if hasattr(sub_control, 'content') and hasattr(sub_control.content, 'value'):
                        if sub_control.content.value == record.original_text:
                            record_index = i
                            break
                if record_index is not None:
                    break

        if record_index is not None:
            # 重新生成这个记录的所有控件
            new_controls = record.to_controls()

            # 移除旧的控件
            for control in reversed(new_controls):
                if control in self.results_list.controls:
                    index = self.results_list.controls.index(control)
                    self.results_list.controls.pop(index)

            # 插入新的控件
            for control in reversed(new_controls):
                self.results_list.controls.insert(record_index, control)

            # 刷新界面
            if self.results_list.page:
                self.results_list.update()

    def add_result(self, text: str, color: Optional[str] = None, is_summary: bool = False):
        """添加新的识别结果（兼容方法）"""
        if not text or text == "点击录音按钮开始...":
            self.clear_result()
        else:
            # 创建新的识别记录
            record_id = self.add_recognition_result(text)
            return record_id

    def set_text(self, text: str, color: Optional[str] = None):
        """设置结果文本（兼容方法）"""
        if not text or text == "点击录音按钮开始...":
            self.clear_result()
        else:
            self.add_recognition_result(text)

    def set_result(self, text: str, color: Optional[str] = None):
        """设置结果文本（兼容方法）"""
        self.set_text(text, color)

    def get_result(self) -> str:
        """获取最后的结果文本（兼容方法）"""
        if self.records:
            return self.records[-1].original_text
        return ""

    def get_recent_results(self, count: int = 3) -> list:
        """获取最近N条结果文本列表（兼容方法）"""
        results = []
        for record in self.records[-count:]:
            results.append(record.original_text)
        return results

    def get_all_results_with_timestamps(self) -> list:
        """获取所有结果（包含时间戳）（兼容方法）"""
        results = []
        for record in self.records:
            results.append({
                "timestamp": record.timestamp.strftime("%H:%M:%S"),
                "text": record.original_text,
                "optimized_text": record.optimized_text,
                "translated_text": record.translated_text,
                "record_id": record.record_id
            })
        return results

    def get_all_recognition_texts(self) -> list:
        """获取所有识别文本（排除汇总报告，仅用于汇总）（兼容方法）"""
        texts = []
        for record in self.records:
            texts.append(record.original_text)
        return texts

    def clear_result(self):
        """清空结果"""
        self.results_list.controls.clear()
        self.records.clear()
        self.record_lookup.clear()
        self._show_empty_state()

    def get_control(self) -> ft.Control:
        """获取Flet控件"""
        return self.card
