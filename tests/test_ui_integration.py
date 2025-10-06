#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI集成测试脚本

测试翻译功能在主应用中的集成
"""

import sys
import os
import time
import threading
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_config_manager_integration():
    """测试配置管理器集成"""
    print("=== 测试配置管理器集成 ===")

    try:
        from utils.config_manager import ConfigManager

        # 创建配置管理器
        config_manager = ConfigManager()

        # 测试新的配置结构
        print(f"翻译功能启用: {config_manager.get('enable_translation', False)}")

        # 测试AI服务配置
        ai_config = config_manager.get_ai_service_config("default")
        print(f"默认AI配置: {ai_config}")

        translation_config = config_manager.get_ai_service_config("translation")
        print(f"翻译AI配置: {translation_config}")

        # 测试Prompt加载
        correction_prompt = config_manager.load_prompt("correction")
        translation_prompt = config_manager.load_prompt("translation")
        print(f"修正Prompt长度: {len(correction_prompt)}")
        print(f"翻译Prompt长度: {len(translation_prompt)}")

        print("配置管理器集成测试通过")

    except Exception as e:
        print(f"配置管理器集成测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_enhanced_settings_dialog():
    """测试增强设置对话框"""
    print("\n=== 测试增强设置对话框 ===")

    try:
        from utils.config_manager import ConfigManager
        from ui.enhanced_settings_dialog import EnhancedSettingsDialog

        # 创建模拟页面对象
        class MockPage:
            def __init__(self):
                self.updated = False

            def update(self):
                self.updated = True

            def open(self, dialog):
                dialog.open = True

        # 创建配置管理器和模拟页面
        config_manager = ConfigManager()
        mock_page = MockPage()

        # 创建设置对话框
        def on_save_callback(settings):
            print(f"设置已保存: {settings.keys()}")

        dialog = EnhancedSettingsDialog(mock_page, config_manager, on_save_callback)

        # 测试对话框创建
        print("增强设置对话框创建成功")
        print(f"支持的标签页数量: {len(dialog.dialog.content.tabs.tabs)}")

        # 测试Prompt重置功能
        dialog._on_reset_prompt(None)
        print("Prompt重置功能测试通过")

        # 测试配置加载
        prompt_type = dialog.prompt_type_dropdown.value
        loaded_prompt = config_manager.load_prompt(prompt_type)
        print(f"Prompt加载测试通过，类型: {prompt_type}, 长度: {len(loaded_prompt)}")

        print("增强设置对话框测试通过")

    except Exception as e:
        print(f"增强设置对话框测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_task_manager_integration():
    """测试任务管理器集成"""
    print("\n=== 测试任务管理器集成 ===")

    try:
        from utils.config_manager import ConfigManager
        from core.task_manager import TaskManager, TranslationTask, AIOptimizationTask

        # 创建配置管理器
        config_manager = ConfigManager()
        config_manager.set("enable_translation", True)
        config_manager.set_ai_service_config("translation", {
            "target_language": "en",
            "system_prompt": "请将以下中文翻译成英文："
        })

        # 创建任务管理器
        task_manager = TaskManager(config_manager=config_manager)
        task_manager.start()

        print("TaskManager启动成功")

        # 测试任务创建
        correction_task = AIOptimizationTask(
            original_text="这是一个测试文本",
            recognition_result={"text": "这是一个测试文本", "confidence": 0.9},
            task_id="test_correction_001",
            created_at=time.time()
        )

        translation_task = TranslationTask(
            original_text="这是一个测试文本",
            source_language="zh",
            target_language="en",
            created_at=time.time()
        )

        print("任务创建成功")

        # 测试队列状态
        queue_status = task_manager.get_queue_status()
        print(f"队列状态: {queue_status}")

        # 测试处理器注册
        processors = task_manager.task_processors
        print(f"注册的处理器: {list(processors.keys())}")

        task_manager.stop()
        print("TaskManager停止成功")

        print("任务管理器集成测试通过")

    except Exception as e:
        print(f"任务管理器集成测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_task_monitor_integration():
    """测试任务监控集成"""
    print("\n=== 测试任务监控集成 ===")

    try:
        from utils.config_manager import ConfigManager
        from core.task_manager import TaskManager
        from ui.task_monitor import TaskMonitor

        # 创建配置管理器和任务管理器
        config_manager = ConfigManager()
        task_manager = TaskManager(config_manager=config_manager)
        task_manager.start()

        # 创建任务监控器
        monitor = TaskMonitor(task_manager)
        ui_container = monitor.build_ui()

        print("任务监控UI创建成功")

        # 测试统计更新
        stats = task_manager.get_statistics()
        monitor._on_statistics_update(stats)
        print("统计更新测试通过")

        # 测试UI更新回调
        test_events = [
            {"type": "recognition_complete", "result": {"text": "测试识别"}},
            {"type": "correction_complete", "result": "测试修正"},
            {"type": "translation_complete", "result": "Test translation"},
            {"type": "error", "error": "测试错误"}
        ]

        for event in test_events:
            monitor._on_ui_update(event)
            print(f"处理事件类型: {event['type']}")

        # 测试日志功能
        print(f"日志条目数量: {len(monitor.log_entries)}")

        task_manager.stop()

        print("任务监控集成测试通过")

    except Exception as e:
        print(f"任务监控集成测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_factory_function():
    """测试工厂函数"""
    print("\n=== 测试工厂函数 ===")

    try:
        from utils.config_manager import ConfigManager
        from ui.dialogs import create_settings_dialog

        # 创建模拟页面对象
        class MockPage:
            def __init__(self):
                self.updated = False

            def update(self):
                self.updated = True

        # 测试工厂函数
        config_manager = ConfigManager()
        mock_page = MockPage()

        def on_save(settings):
            pass

        # 使用工厂函数创建设置对话框
        dialog = create_settings_dialog(mock_page, config_manager, on_save)

        print("工厂函数成功创建设置对话框")
        print(f"对话框类型: {type(dialog).__name__}")

        print("工厂函数测试通过")

    except Exception as e:
        print(f"工厂函数测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("开始UI集成测试...")

    try:
        test_config_manager_integration()
        test_enhanced_settings_dialog()
        test_task_manager_integration()
        test_task_monitor_integration()
        test_factory_function()

        print("\n所有UI集成测试完成！")

    except Exception as e:
        print(f"\nUI集成测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()