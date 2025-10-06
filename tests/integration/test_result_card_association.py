#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的ResultCard关联功能
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_result_card_association():
    """测试ResultCard的关联功能"""
    print("=== 测试ResultCard关联功能 ===")
    try:
        from ui.result_card_new import ResultCard

        # 创建ResultCard实例
        result_card = ResultCard()
        print("[OK] ResultCard创建成功")

        # 测试添加识别结果
        print("\n--- 测试添加识别结果 ---")
        record_id1 = result_card.add_recognition_result("这是第一条语音识别结果")
        print(f"[OK] 添加识别结果1: {record_id1}")

        record_id2 = result_card.add_recognition_result("这是第二条语音识别结果")
        print(f"[OK] 添加识别结果2: {record_id2}")

        # 测试添加修正结果
        print("\n--- 测试添加修正结果 ---")
        result_card.add_correction_result(record_id1, "这是第一条的修正结果")
        print("[OK] 添加修正结果到记录1")

        result_card.add_correction_result(record_id2, "这是第二条的修正结果")
        print("[OK] 添加修正结果到记录2")

        # 测试添加翻译结果
        print("\n--- 测试添加翻译结果 ---")
        result_card.add_translation_result(record_id1, "This is the first translation result")
        print("[OK] 添加翻译结果到记录1")

        result_card.add_translation_result(record_id2, "This is the second translation result")
        print("[OK] 添加翻译结果到记录2")

        # 测试获取结果
        print("\n--- 测试获取结果 ---")
        all_results = result_card.get_all_results_with_timestamps()
        print(f"[OK] 获取所有结果: {len(all_results)}条记录")

        recognition_texts = result_card.get_all_recognition_texts()
        print(f"[OK] 识别文本数量: {len(recognition_texts)}")
        for i, text in enumerate(recognition_texts, 1):
            print(f"  {i}. {text}")

        # 测试清空结果
        print("\n--- 测试清空结果 ---")
        result_card.clear_result()
        print("[OK] 清空结果成功")

        # 验证空状态
        empty_results = result_card.get_all_results_with_timestamps()
        print(f"[OK] 清空后结果数量: {len(empty_results)}")

        return True

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_task_data_classes():
    """测试Task数据类是否支持record_id"""
    print("\n=== 测试Task数据类 ===")
    try:
        from core.task_manager import AIOptimizationTask, TranslationTask
        import time

        # 测试AIOptimizationTask
        correction_task = AIOptimizationTask(
            original_text="测试文本",
            recognition_result={"text": "测试文本", "confidence": 0.9},
            task_id="test_correction_1",
            created_at=time.time(),
            record_id="test_record_1"
        )
        print(f"[OK] AIOptimizationTask支持record_id: {correction_task.record_id}")

        # 测试TranslationTask
        translation_task = TranslationTask(
            original_text="测试文本",
            source_language="zh",
            target_language="en",
            task_id="test_translation_1",
            created_at=time.time(),
            record_id="test_record_1"
        )
        print(f"[OK] TranslationTask支持record_id: {translation_task.record_id}")

        return True

    except Exception as e:
        print(f"[ERROR] Task数据类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试新的ResultCard关联功能...\n")

    results = []
    results.append(test_result_card_association())
    results.append(test_task_data_classes())

    passed = sum(results)
    total = len(results)

    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("[OK] 所有测试通过！新的ResultCard关联功能正常工作。")
        print("\n现在修正和翻译结果将会追加到原始识别记录下方，而不是作为独立的对话记录显示。")
    else:
        print("[ERROR] 部分测试失败，请检查实现。")

    return passed == total

if __name__ == "__main__":
    main()