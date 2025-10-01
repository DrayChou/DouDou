#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务监控UI组件

实时显示多线程任务处理状态和统计信息
"""

import time
import threading
from typing import Optional, Dict, Any

import flet as ft

try:
    # 尝试相对导入（开发环境）
    from ..core.task_manager import TaskManager, TaskStatistics
except ImportError:
    # 回退到绝对导入（打包环境）
    from core.task_manager import TaskManager, TaskStatistics


class TaskMonitor:
    """任务池监控器 - UI组件"""

    def __init__(self, task_manager: TaskManager):
        """
        初始化任务监控器

        Args:
            task_manager: 任务管理器实例
        """
        self.task_manager = task_manager
        self.is_visible = True

        # 统计数据
        self.current_stats = TaskStatistics()
        self.last_update_time = time.time()

        # UI控件
        self.status_container: Optional[ft.Container] = None
        self.progress_audio: Optional[ft.ProgressRing] = None
        self.progress_recognition: Optional[ft.ProgressRing] = None
        self.progress_ai: Optional[ft.ProgressRing] = None

        # 统计文本控件
        self.audio_count_text: Optional[ft.Text] = None
        self.recognition_count_text: Optional[ft.Text] = None
        self.ai_count_text: Optional[ft.Text] = None
        self.total_count_text: Optional[ft.Text] = None
        self.success_rate_text: Optional[ft.Text] = None
        self.uptime_text: Optional[ft.Text] = None

        # 日志列表
        self.log_list: Optional[ft.ListView] = None
        self.log_entries = []

        # 更新线程
        self.update_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # 注册回调
        self.task_manager.on_statistics_update = self._on_statistics_update
        self.task_manager.on_ui_update = self._on_ui_update

    def build_ui(self) -> ft.Container:
        """构建任务监控UI"""
        # 创建进度指示器
        self.progress_audio = ft.ProgressRing(
            width=20,
            height=20,
            color=ft.Colors.BLUE,
            bgcolor=ft.Colors.BLUE_50
        )

        self.progress_recognition = ft.ProgressRing(
            width=20,
            height=20,
            color=ft.Colors.GREEN,
            bgcolor=ft.Colors.GREEN_50
        )

        self.progress_ai = ft.ProgressRing(
            width=20,
            height=20,
            color=ft.Colors.ORANGE,
            bgcolor=ft.Colors.ORANGE_50
        )

        # 创建统计文本
        self.audio_count_text = ft.Text("0", size=12, width=30, text_align=ft.TextAlign.CENTER)
        self.recognition_count_text = ft.Text("0", size=12, width=30, text_align=ft.TextAlign.CENTER)
        self.ai_count_text = ft.Text("0", size=12, width=30, text_align=ft.TextAlign.CENTER)
        self.total_count_text = ft.Text("0", size=12, weight=ft.FontWeight.BOLD)
        self.success_rate_text = ft.Text("0%", size=12, color=ft.Colors.GREEN)
        self.uptime_text = ft.Text("00:00:00", size=11, color=ft.Colors.GREY_600)

        # 创建日志列表
        self.log_list = ft.ListView(
            height=120,
            spacing=2,
            auto_scroll=True,
            expand=True
        )

        # 构建主容器
        self.status_container = ft.Container(
            content=ft.Column([
                # 标题栏
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.MONITOR_HEART, color=ft.Colors.BLUE_500, size=16),
                        ft.Text("任务监控", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        ft.Container(
                            content=self.uptime_text,
                            padding=ft.padding.symmetric(horizontal=8),
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=12
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=ft.border_radius.only(top_left=8, top_right=8)
                ),

                # 任务状态行
                ft.Container(
                    content=ft.Column([
                        self._build_task_status_row("录音", self.progress_audio, self.audio_count_text, ft.Colors.BLUE),
                        ft.Container(height=4),
                        self._build_task_status_row("识别", self.progress_recognition, self.recognition_count_text, ft.Colors.GREEN),
                        ft.Container(height=4),
                        self._build_task_status_row("AI优化", self.progress_ai, self.ai_count_text, ft.Colors.ORANGE),
                        ft.Divider(height=1, color=ft.Colors.GREY_300),
                        ft.Container(
                            content=ft.Row([
                                ft.Text("总计:", size=12, weight=ft.FontWeight.BOLD),
                                self.total_count_text,
                                ft.Container(width=10),
                                ft.Text("成功率:", size=12),
                                self.success_rate_text,
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(vertical=4)
                        ),
                    ]),
                    padding=ft.padding.all(10)
                ),

                # 日志区域
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.LIST, color=ft.Colors.GREY_600, size=14),
                                ft.Text("处理日志", size=12, color=ft.Colors.GREY_700),
                                ft.Container(
                                    content=ft.ElevatedButton(
                                        "清空",
                                        on_click=self._clear_logs,
                                        width=50,
                                        height=25,
                                        style=ft.ButtonStyle(
                                            text_style=ft.TextStyle(size=10)
                                        )
                                    ),
                                    alignment=ft.alignment.center
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(horizontal=10, vertical=5)
                        ),
                        ft.Container(
                            content=self.log_list,
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            bgcolor=ft.Colors.GREY_50,
                            border_radius=4
                        )
                    ]),
                    expand=True
                ),

            ], spacing=0),
            width=300,
            height=400,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.GREY_200)
        )

        return self.status_container

    def _build_task_status_row(self, label: str, progress_ring: ft.ProgressRing,
                              count_text: ft.Text, color) -> ft.Row:
        """构建任务状态行"""
        # 创建带透明度的背景色
        # ft.Colors常量返回的是字符串颜色值（如"#2196F3"），添加透明度
        if isinstance(color, str) and color.startswith("#"):
            bg_color = f"{color}20"  # 添加20透明度 (约12%)
        else:
            bg_color = ft.Colors.GREY_100

        return ft.Row([
            ft.Text(label, size=12, width=40, color=color),
            progress_ring,
            ft.Container(width=8),
            count_text,
            ft.Container(
                content=ft.Text("处理中", size=10, color=color),
                width=40,
                height=16,
                bgcolor=bg_color,
                border_radius=8,
                alignment=ft.alignment.center,
                key=f"{label}_status"
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def _on_statistics_update(self, stats: TaskStatistics):
        """统计更新回调"""
        if not self.is_visible:
            return

        # 更新统计信息
        self.current_stats = stats
        self.last_update_time = time.time()

        # 计算总待处理数
        total_pending = (stats.audio_pending + stats.recognition_pending + stats.ai_pending)
        total_processing = (stats.audio_processing + stats.recognition_processing + stats.ai_processing)

        # 更新进度环
        self._update_progress_ring(self.progress_audio, stats.audio_processing, total_pending + total_processing)
        self._update_progress_ring(self.progress_recognition, stats.recognition_processing, total_pending + total_processing)
        self._update_progress_ring(self.progress_ai, stats.ai_processing, total_pending + total_processing)

        # 更新计数文本 - 显示 (待处理+处理中) 的数量
        self.audio_count_text.value = str(stats.audio_pending + stats.audio_processing)
        self.recognition_count_text.value = str(stats.recognition_pending + stats.recognition_processing)
        self.ai_count_text.value = str(stats.ai_pending + stats.ai_processing)

        # 更新总计和成功率
        total_count = stats.total_processed + stats.total_failed
        self.total_count_text.value = str(total_count)
        self.success_rate_text.value = f"{stats.success_rate * 100:.1f}%"
        self.success_rate_text.color = ft.Colors.GREEN if stats.success_rate > 0.8 else ft.Colors.ORANGE

        # 更新运行时间
        uptime_seconds = int(stats.uptime)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        self.uptime_text.value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _update_progress_ring(self, progress_ring: ft.ProgressRing, current: int, total: int):
        """更新进度环"""
        if total > 0:
            progress_ring.value = current / total
        else:
            progress_ring.value = 0.0

    def _on_ui_update(self, update_data: Dict[str, Any]):
        """UI更新回调"""
        if not self.is_visible:
            return

        update_type = update_data.get('type', '')
        timestamp = time.strftime("%H:%M:%S")

        if update_type == 'ai_optimization_complete':
            self._add_log_entry(
                timestamp=timestamp,
                message=f"AI优化完成: {update_data.get('optimized_text', 'N/A')[:30]}...",
                color=ft.Colors.GREEN,
                icon=ft.Icons.CHECK_CIRCLE
            )
        elif update_type == 'recognition_complete':
            self._add_log_entry(
                timestamp=timestamp,
                message=f"识别完成: {update_data.get('result', {}).get('text', 'N/A')[:30]}...",
                color=ft.Colors.BLUE,
                icon=ft.Icons.RECORD_VOICE_OVER
            )
        elif update_type == 'error':
            self._add_log_entry(
                timestamp=timestamp,
                message=f"错误: {update_data.get('error', 'Unknown error')}",
                color=ft.Colors.RED,
                icon=ft.Icons.ERROR
            )

    def _add_log_entry(self, timestamp: str, message: str, color, icon):
        """添加日志条目"""
        # 创建淡背景色
        if isinstance(color, str) and color.startswith("#"):
            bg_color = f"{color}10"  # 添加10透明度 (约6%)
        else:
            bg_color = ft.Colors.GREY_50

        log_entry = ft.Container(
            content=ft.Row([
                ft.Text(timestamp, size=10, color=ft.Colors.GREY_600, width=50),
                ft.Icon(icon, color=color, size=12),
                ft.Container(
                    expand=True,  # 使用expand代替Expanded
                    content=ft.Text(
                        message,
                        size=11,
                        color=ft.Colors.BLACK87,
                        selectable=True
                    )
                ),
            ], spacing=4),
            padding=ft.padding.symmetric(horizontal=4, vertical=2),
            bgcolor=bg_color,
            border_radius=4
        )

        self.log_entries.append(log_entry)
        self.log_list.controls.append(log_entry)

        # 限制日志条目数量
        max_entries = 50
        if len(self.log_entries) > max_entries:
            oldest_entry = self.log_entries.pop(0)
            self.log_list.controls.remove(oldest_entry)

    def _clear_logs(self, e=None):
        """清空日志"""
        self.log_entries.clear()
        self.log_list.controls.clear()
        self.log_list.update()

    def set_visibility(self, visible: bool):
        """设置可见性"""
        self.is_visible = visible
        if self.status_container:
            self.status_container.visible = visible
            self.status_container.update()

    def start_monitoring(self):
        """开始监控"""
        self.stop_event.clear()
        if not self.update_thread or not self.update_thread.is_alive():
            self.update_thread = threading.Thread(
                target=self._monitoring_loop,
                name="TaskMonitor",
                daemon=True
            )
            self.update_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.stop_event.set()
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)

    def _monitoring_loop(self):
        """监控循环"""
        while not self.stop_event.is_set():
            try:
                if self.is_visible and self.task_manager.is_running:
                    # 定期更新统计信息
                    stats = self.task_manager.get_statistics()
                    self._on_statistics_update(stats)

                time.sleep(1.0)  # 每秒更新一次

            except Exception as e:
                print(f"监控循环异常: {e}")
                time.sleep(1.0)

    def get_control(self) -> ft.Container:
        """获取UI控件"""
        return self.status_container or self.build_ui()

    def __del__(self):
        """析构函数"""
        self.stop_monitoring()