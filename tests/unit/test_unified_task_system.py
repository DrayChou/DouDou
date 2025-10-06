#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统一任务系统
"""

import sys
import os
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class MockAudioSegment:
    """模拟音频片段"""
    def __init__(self, text="测试音频"):
        self.text = text
        self.duration = 2.0

    def get_audio_data(self):
        return b"mock_audio_data"

def test_unified_task_system():
    """测试统一任务系统"""
    print("=== 测试统一任务系统 ===")
    try:
        from core.unified_task_system import UnifiedTaskSystem, TaskStatus
        from utils.config_manager import ConfigManager

        config_manager = ConfigManager()
        task_system = UnifiedTaskSystem(config_manager=config_manager)
        print("[OK] 统一任务系统创建成功")

        # 设置回调
        recognition_results = []
        correction_results = []
        translation_results = []

        def on_recognition(task):
            print(f"[识别完成] {task.recognized_text}")
            recognition_results.append(task.recognized_text)

        def on_correction(task):
            print(f"[修正完成] {task.corrected_text}")
            correction_results.append(task.corrected_text)

        def on_translation(task):
            print(f"[翻译完成] {task.translated_text}")
            translation_results.append(task.translated_text)

        def on_complete(task):
            print(f"[任务完成] 状态: {task.status.value}")

        task_system.on_recognition_complete = on_recognition
        task_system.on_correction_complete = on_correction
        task_system.on_translation_complete = on_translation
        task_system.on_task_complete = on_complete

        # 启动系统
        task_system.start()
        print("[OK] 任务系统启动成功")

        # 提交几个任务
        print("\n--- 提交测试任务 ---")
        audio_segments = [
            MockAudioSegment("这是第一个测试"),
            MockAudioSegment("这是第二个测试"),
            MockAudioSegment("这是第三个测试")
        ]

        task_ids = []
        for i, audio in enumerate(audio_segments):
            task_id = task_system.submit_task(
                audio_segment=audio,
                record_id=f"test_record_{i}",
                enable_correction=True,
                enable_translation=True
            )
            task_ids.append(task_id)
            print(f"[OK] 提交任务: {task_id}")

        # 等待任务完成
        print("\n--- 等待任务完成 ---")
        start_time = time.time()
        max_wait_time = 60  # 最多等待60秒

        while time.time() - start_time < max_wait_time:
            stats = task_system.get_statistics()
            if stats['active_tasks'] == 0:
                break
            print(f"[统计] 活跃任务: {stats['active_tasks']}, "
                  f"已完成: {stats['completed_tasks']}, "
                  f"失败: {stats['failed_tasks']}, "
                  f"超时: {stats['timeout_tasks']}")
            time.sleep(2)

        # 检查结果
        print(f"\n--- 测试结果 ---")
        stats = task_system.get_statistics()
        print(f"总任务数: {stats['total_tasks']}")
        print(f"完成任务数: {stats['completed_tasks']}")
        print(f"失败任务数: {stats['failed_tasks']}")
        print(f"超时任务数: {stats['timeout_tasks']}")

        print(f"\n识别结果数量: {len(recognition_results)}")
        print(f"修正结果数量: {len(correction_results)}")
        print(f"翻译结果数量: {len(translation_results)}")

        # 停止系统
        task_system.stop()
        print("[OK] 任务系统停止成功")

        return stats['completed_tasks'] > 0

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_task_adapter():
    """测试任务适配器"""
    print("\n=== 测试任务适配器 ===")
    try:
        from core.task_adapter import TaskManagerAdapter, create_task_manager
        from utils.config_manager import ConfigManager

        config_manager = ConfigManager()

        # 测试直接创建适配器
        adapter = TaskManagerAdapter(config_manager=config_manager)
        print("[OK] 任务适配器创建成功")

        # 测试工厂函数
        task_manager = create_task_manager(use_unified_system=True, config_manager=config_manager)
        print("[OK] 工厂函数创建成功")

        return True

    except Exception as e:
        print(f"[ERROR] 适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试统一任务系统...\n")

    results = []
    results.append(test_unified_task_system())
    results.append(test_task_adapter())

    passed = sum(results)
    total = len(results)

    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("[OK] 所有测试通过！新的统一任务系统正常工作。")
        print("\n新系统的优势：")
        print("1. 任务生命周期统一管理")
        print("2. 自动去重机制")
        print("3. 超时控制")
        print("4. 限制并发AI任务数")
        print("5. 级联任务管理")
    else:
        print("[ERROR] 部分测试失败，请检查实现。")

    return passed == total

if __name__ == "__main__":
    main()