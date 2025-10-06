#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果显示卡片（重新设计）

支持关联的识别、修正、翻译结果展示
"""

import flet as ft
from typing import Optional
from datetime import datetime


class ResultRecord:
    """单条记录（原文 + 可选修正 + 可选翻译）"""

    def __init__(self, original_text: str, record_id: Optional[str] = None):
        self.original_text = original_text
        self.record_id = record_id or f"record_{int(datetime.now().timestamp() * 1000)}"
        self.optimized_text: Optional[str] = None
        self.translated_text: Optional[str] = None
        self.target_language: Optional[str] = None
        self.timestamp = datetime.now()
        self.controls = []  # 缓存对应的UI控件

    def add_correction(self, text: str):
        self.optimized_text = text

    def add_translation(self, text: str, target_language: Optional[str] = None):
        self.translated_text = text
        if target_language:
            self.target_language = target_language

    def _target_lang_name(self) -> str:
        lang_map = {
            "en": "英文", "ja": "日文", "ko": "韩文", "fr": "法文",
            "de": "德文", "es": "西班牙文", "ru": "俄文", "it": "意大利文", "pt": "葡萄牙文",
        }
        if self.target_language:
            return lang_map.get(self.target_language, self.target_language)
        return "翻译"

    def to_controls(self) -> list:
        controls = []

        # 原文
        controls.append(ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(self.timestamp.strftime("%H:%M:%S"), size=11, color=ft.Colors.GREY_500, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=4),
                ft.Text(self.original_text, size=13, color=ft.Colors.BLACK87, selectable=True),
            ]),
            padding=ft.padding.all(12),
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200),
        ))

        # 修正
        if self.optimized_text:
            controls.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("[AI修正]", size=11, color=ft.Colors.ORANGE_700, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Container(height=2),
                    ft.Text(self.optimized_text, size=13, color=ft.Colors.BLACK87, selectable=True),
                ]),
                padding=ft.padding.only(left=20, right=12, top=8, bottom=8),
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=8,
                border=ft.border.only(left=ft.BorderSide(width=4, color=ft.Colors.ORANGE_300)),
            ))

        # 翻译
        if self.translated_text:
            controls.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"[翻译 → {self._target_lang_name()}]", size=11, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Container(height=2),
                    ft.Text(self.translated_text, size=13, color=ft.Colors.BLACK87, selectable=True),
                ]),
                padding=ft.padding.only(left=20, right=12, top=8, bottom=8),
                bgcolor=ft.Colors.GREEN_50,
                border_radius=8,
                border=ft.border.only(left=ft.BorderSide(width=4, color=ft.Colors.GREEN_300)),
            ))

        return controls


class ResultCard:
    """结果卡片：负责管理 ResultRecord 并渲染到列表"""

    def __init__(self):
        self.results_list = ft.Column(spacing=8, expand=True, scroll=ft.ScrollMode.AUTO)
        self.empty_text = ft.Text("点击录音按钮开始...", size=13, color=ft.Colors.GREY_600, selectable=True)
        self.card = ft.Card(content=ft.Container(padding=16, content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.TEXT_FORMAT, color=ft.Colors.BLUE_500, size=16),
                ft.Text("识别结果", size=16, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Divider(height=8),
            self.results_list,
        ], horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.AUTO)), elevation=2, expand=True)

        self.records: list[ResultRecord] = []
        self.record_lookup: dict[str, ResultRecord] = {}
        self._show_empty_state()

    def _show_empty_state(self):
        self.results_list.controls = [ft.Container(content=self.empty_text, alignment=ft.alignment.center)]

    def add_recognition_result(self, text: str, record_id: Optional[str] = None) -> str:
        # 清空空状态
        if len(self.results_list.controls) == 1 and getattr(getattr(self.results_list.controls[0], 'content', None), 'value', None) == "点击录音按钮开始...":
            self.results_list.controls.clear()

        record = ResultRecord(text, record_id)
        self.records.append(record)
        self.record_lookup[record.record_id] = record

        ctrls = record.to_controls()
        record.controls = ctrls
        for c in ctrls:
            self.results_list.controls.insert(0, c)

        if self.results_list.page:
            self.results_list.scroll_to(offset=0, duration=200)

        return record.record_id

    def add_correction_result(self, record_id: str, optimized_text: str):
        rec = self.record_lookup.get(record_id)
        if not rec:
            return
        rec.add_correction(optimized_text)
        self._refresh_record(rec)

    def add_translation_result(self, record_id: str, translated_text: str, target_language: Optional[str] = None):
        rec = self.record_lookup.get(record_id)
        if not rec:
            return
        rec.add_translation(translated_text, target_language)
        self._refresh_record(rec)

    def _refresh_record(self, rec: ResultRecord):
        if not rec.controls:
            self._refresh_record_legacy(rec)
            return
        try:
            first = rec.controls[0]
            idx = self.results_list.controls.index(first)
        except (ValueError, IndexError):
            return

        # 删除旧控件
        for c in rec.controls:
            if c in self.results_list.controls:
                self.results_list.controls.remove(c)

        new_ctrls = rec.to_controls()
        rec.controls = new_ctrls
        for i, c in enumerate(new_ctrls):
            self.results_list.controls.insert(idx + i, c)
        if self.results_list.page:
            self.results_list.update()

    def _refresh_record_legacy(self, rec: ResultRecord):
        # 兼容：通过查找原文控件定位，较慢
        rec_index = None
        for i, ctrl in enumerate(self.results_list.controls):
            if hasattr(ctrl, 'content') and hasattr(ctrl.content, 'controls'):
                for sub in ctrl.content.controls:
                    if getattr(getattr(sub, 'content', None), 'value', None) == rec.original_text:
                        rec_index = i
                        break
                if rec_index is not None:
                    break
        if rec_index is None:
            return
        new_ctrls = rec.to_controls()
        # 移除旧
        for c in list(self.results_list.controls):
            if c in new_ctrls:
                self.results_list.controls.remove(c)
        # 插入新
        for c in reversed(new_ctrls):
            self.results_list.controls.insert(rec_index, c)
        if self.results_list.page:
            self.results_list.update()

    # 兼容方法
    def add_result(self, text: str, color: Optional[str] = None, is_summary: bool = False):
        return self.add_recognition_result(text)

    def set_text(self, text: str, color: Optional[str] = None):
        if not text or text == "点击录音按钮开始...":
            self.clear_result()
        else:
            self.add_recognition_result(text)

    def set_result(self, text: str, color: Optional[str] = None):
        self.set_text(text, color)

    def get_result(self) -> str:
        if self.records:
            return self.records[-1].original_text
        return ""

    def get_recent_results(self, count: int = 3) -> list:
        return [r.original_text for r in self.records[-count:]]

    def get_all_results_with_timestamps(self) -> list:
        return [{
            "timestamp": r.timestamp.strftime("%H:%M:%S"),
            "text": r.original_text,
            "optimized_text": r.optimized_text,
            "translated_text": r.translated_text,
            "record_id": r.record_id,
        } for r in self.records]

    def get_all_recognition_texts(self) -> list:
        return [r.original_text for r in self.records]

    def clear_result(self):
        self.results_list.controls.clear()
        self.records.clear()
        self.record_lookup.clear()
        self._show_empty_state()

    def get_control(self) -> ft.Control:
        return self.card

