#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试UI回调函数的脚本
"""

import sys
import os
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ui_callbacks():
    """测试UI回调函数"""
    print("=== 测试UI回调函数 ===")
    try:
        from core.task_manager import TaskManager, AIOptimizationTask, TranslationTask
        from utils.config_manager import ConfigManager
        from utils.logger import get_logger

        logger = get_logger()
        config_manager = ConfigManager()

        # 模拟UI回调函数
        def on_correction_complete(task):
            print(f"[UI回调] 修正完成: {task.optimized_text}")
            logger.info(f"[UI回调] 修正完成: {task.optimized_text}")

        def on_translation_complete(task):
            print(f"[UI回调] 翻译完成: {task.translated_text}")
            logger.info(f"[UI回调] 翻译完成: {task.translated_text}")

        # 创建TaskManager并设置回调
        task_manager = TaskManager(funasr_recognizer=None, config_manager=config_manager)
        task_manager.on_correction_complete = on_correction_complete
        task_manager.on_translation_complete = on_translation_complete
        task_manager.start()

        print(f"[OK] TaskManager创建并设置回调")

        # 测试修正任务
        print("\n--- 测试修正任务 ---")
        correction_task = AIOptimizationTask(
            original_text="这是一个测试语音识别结果",
            recognition_result={"text": "这是一个测试语音识别结果", "confidence": 0.9},
            task_id=f"test_correction_{int(time.time() * 1000)}",
            created_at=time.time()
        )

        future = task_manager.submit_correction_task(correction_task)
        result = future.result(timeout=30)
        print(f"[OK] 修正任务结果: {result}")

        # 等待一下让回调执行
        time.sleep(1)

        # 测试翻译任务
        print("\n--- 测试翻译任务 ---")
        translation_task = TranslationTask(
            original_text="这是一个测试文本",
            source_language="zh",
            target_language="ja",
            created_at=time.time()
        )

        future = task_manager.submit_translation_task(translation_task)
        result = future.result(timeout=30)
        print(f"[OK] 翻译任务结果: {result}")

        # 等待一下让回调执行
        time.sleep(1)

        task_manager.stop()
        return True

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试UI回调函数...\n")

    success = test_ui_callbacks()

    if success:
        print("\n[OK] UI回调函数测试通过！")
    else:
        print("\n[ERROR] UI回调函数测试失败。")

    return success

if __name__ == "__main__":
    main()