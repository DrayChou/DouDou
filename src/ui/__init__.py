#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户界面模块
包含 Flet UI 组件、布局管理、对话框等
"""

try:
    # 尝试相对导入（开发环境）
    from .components import (
        RecordButton,
        StatusDisplay,
        AudioVisualization,
        ResultCard,
        ActionButtons,
        AudioDeviceSelector,
        RealtimeModeToggle,
    )
    from .dialogs import SettingsDialog, HelpDialog
    from .task_monitor import TaskMonitor
except ImportError:
    # 回退到绝对导入（打包环境）
    from ui.components import (
        RecordButton,
        StatusDisplay,
        AudioVisualization,
        ResultCard,
        ActionButtons,
        AudioDeviceSelector,
        RealtimeModeToggle,
    )
    from ui.dialogs import SettingsDialog, HelpDialog
    from ui.task_monitor import TaskMonitor

__all__ = [
    "RecordButton",
    "StatusDisplay",
    "AudioVisualization",
    "ResultCard",
    "ActionButtons",
    "AudioDeviceSelector",
    "RealtimeModeToggle",
    "SettingsDialog",
    "HelpDialog",
    "TaskMonitor",
]