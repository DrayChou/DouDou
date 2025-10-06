#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修正任务处理

验证AI修正任务是否能够被正确执行
"""

import sys
import os
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_correction_task():
    """测试修正任务处理"""
    from core.task_manager import TaskManager, AIOptimizationTask
    from utils.config_manager import ConfigManager

    print("=== 测试AI修正任务处理 ===\n")

    # 初始化
    config_manager = ConfigManager()
    task_manager = TaskManager(funasr_recognizer=None, config_manager=config_manager)

    # 设置回调
    results = []
    def on_correction_complete(task):
        print(f"[CALLBACK] 修正完成: {task.optimized_text}")
        results.append(task)

    task_manager.on_correction_complete = on_correction_complete

    # 启动TaskManager
    task_manager.start()
    print(f"TaskManager已启动: {task_manager.is_running}\n")

    # 创建测试任务
    test_task = AIOptimizationTask(
        original_text="这是一个测试文本",
        recognition_result={'text': '这是一个测试文本', 'confidence': 0.9},
        task_id=f"test_{int(time.time() * 1000)}",
        created_at=time.time()
    )

    print(f"创建测试任务: {test_task.task_id}")
    print(f"原文: {test_task.original_text}\n")

    # 提交任务
    try:
        future = task_manager.submit_correction_task(test_task)
        print(f"任务已提交，future: {future}")
        print(f"等待任务完成...\n")

        # 等待结果（最多30秒）
        result = future.result(timeout=30)
        print(f"任务执行结果: {result}")

    except Exception as e:
        print(f"[ERROR] 任务执行失败: {e}")
        import traceback
        traceback.print_exc()

    # 等待回调
    time.sleep(2)

    # 检查结果
    print(f"\n=== 测试结果 ===")
    print(f"回调触发次数: {len(results)}")
    if results:
        print(f"修正后文本: {results[0].optimized_text}")
        print("[OK] 测试通过")
    else:
        print("[FAIL] 回调未被触发")

    # 停止TaskManager
    task_manager.stop()

if __name__ == "__main__":
    test_correction_task()
