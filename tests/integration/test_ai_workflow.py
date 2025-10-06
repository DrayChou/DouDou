#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI修正和翻译工作流程
"""

import sys
import os
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ai_correction_workflow():
    """测试AI修正工作流程"""
    print("=== 测试AI修正工作流程 ===")
    try:
        from core.task_manager import TaskManager, AIOptimizationTask
        from utils.config_manager import ConfigManager

        config_manager = ConfigManager()
        print(f"[OK] ConfigManager创建成功")

        # 检查AI配置
        ai_config = config_manager.get_ai_service_config("correction")
        print(f"[DEBUG] AI配置: {ai_config}")

        # 创建TaskManager
        task_manager = TaskManager(funasr_recognizer=None, config_manager=config_manager)
        task_manager.start()
        print(f"[OK] TaskManager启动成功")

        # 创建测试修正任务
        correction_task = AIOptimizationTask(
            original_text="这是一个测试语音识别结果",
            recognition_result={"text": "这是一个测试语音识别结果", "confidence": 0.9},
            task_id=f"test_correction_{int(time.time() * 1000)}",
            created_at=time.time()
        )
        print(f"[OK] 修正任务创建成功")

        # 提交修正任务
        future = task_manager.submit_correction_task(correction_task)
        print(f"[OK] 修正任务提交成功")

        # 等待任务完成
        try:
            result = future.result(timeout=30)  # 等待30秒
            print(f"[OK] 修正任务完成: {result}")
            return True
        except Exception as e:
            print(f"[ERROR] 修正任务执行失败: {e}")
            return False

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'task_manager' in locals():
            task_manager.stop()

def test_ai_translation_workflow():
    """测试AI翻译工作流程"""
    print("\n=== 测试AI翻译工作流程 ===")
    try:
        from core.task_manager import TaskManager, TranslationTask
        from utils.config_manager import ConfigManager

        config_manager = ConfigManager()
        print(f"[OK] ConfigManager创建成功")

        # 检查翻译配置
        translation_config = config_manager.get_ai_service_config("translation")
        print(f"[DEBUG] 翻译配置: {translation_config}")

        # 创建TaskManager
        task_manager = TaskManager(funasr_recognizer=None, config_manager=config_manager)
        task_manager.start()
        print(f"[OK] TaskManager启动成功")

        # 创建测试翻译任务
        translation_task = TranslationTask(
            original_text="这是一个测试文本",
            source_language="zh",
            target_language=translation_config.get("target_language", "en"),
            created_at=time.time()
        )
        print(f"[OK] 翻译任务创建成功")

        # 提交翻译任务
        future = task_manager.submit_translation_task(translation_task)
        print(f"[OK] 翻译任务提交成功")

        # 等待任务完成
        try:
            result = future.result(timeout=30)  # 等待30秒
            print(f"[OK] 翻译任务完成: {result}")
            return True
        except Exception as e:
            print(f"[ERROR] 翻译任务执行失败: {e}")
            return False

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'task_manager' in locals():
            task_manager.stop()

def main():
    """主测试函数"""
    print("开始测试AI修正和翻译工作流程...\n")

    results = []
    results.append(test_ai_correction_workflow())
    results.append(test_ai_translation_workflow())

    passed = sum(results)
    total = len(results)

    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("[OK] 所有测试通过！AI工作流程正常。")
    else:
        print("[ERROR] 部分测试失败，AI工作流程有问题。")

    return passed == total

if __name__ == "__main__":
    main()