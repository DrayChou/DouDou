#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置修复的脚本

验证TaskManager是否能正确传递config_manager
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config_manager_passing():
    """测试config_manager传递"""
    print("=== 测试TaskManager配置传递 ===")
    try:
        from core.task_manager import TaskManager
        from utils.config_manager import ConfigManager

        config_manager = ConfigManager()
        print(f"[OK] ConfigManager创建成功")
        print(f"[DEBUG] 配置文件路径: {config_manager.config_file}")

        # 测试AI配置
        ai_config = config_manager.get_ai_service_config("correction")
        print(f"[DEBUG] Correction AI配置: {ai_config}")

        # 创建TaskManager并传入config_manager
        task_manager = TaskManager(funasr_recognizer=None, config_manager=config_manager)
        print(f"[OK] TaskManager创建成功")
        print(f"[DEBUG] TaskManager.config_manager存在: {task_manager.config_manager is not None}")

        # 启动TaskManager
        task_manager.start()
        print(f"[OK] TaskManager启动成功，运行状态: {task_manager.is_running}")

        # 测试处理器创建
        from core.task_processors import TaskProcessorRegistry
        processor = TaskProcessorRegistry.get_processor("correction")
        print(f"[OK] Correction处理器获取成功: {processor}")

        # 停止TaskManager
        task_manager.stop()
        print(f"[OK] TaskManager停止成功")

        return True
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_correction_processor():
    """测试修正处理器配置"""
    print("\n=== 测试CorrectionProcessor配置 ===")
    try:
        from core.task_processors.correction_processor import CorrectionProcessor
        from utils.config_manager import ConfigManager

        config_manager = ConfigManager()
        base_config = config_manager.get_all()
        print(f"[DEBUG] 基础配置键: {list(base_config.keys())}")

        processor = CorrectionProcessor()

        # 测试配置验证
        is_valid = processor.validate_config(base_config)
        print(f"[DEBUG] 配置验证结果: {is_valid}")

        if not is_valid:
            print(f"[ERROR] 配置验证失败: {processor.last_error}")
        else:
            print(f"[OK] 配置验证成功")

            # 测试AI配置获取
            ai_config = processor.get_ai_config(base_config)
            print(f"[DEBUG] AI配置: {ai_config}")

            # 测试prompt获取
            prompt = processor.get_prompt(base_config)
            print(f"[DEBUG] Prompt长度: {len(prompt)}")

        return is_valid
    except Exception as e:
        print(f"[ERROR] CorrectionProcessor测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试配置修复...\n")

    results = []
    results.append(test_config_manager_passing())
    results.append(test_correction_processor())

    passed = sum(results)
    total = len(results)

    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("[OK] 所有测试通过！配置修复成功。")
    else:
        print("[ERROR] 部分测试失败，需要进一步调试。")

    return passed == total

if __name__ == "__main__":
    main()