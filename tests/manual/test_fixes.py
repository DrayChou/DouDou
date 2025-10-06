#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复功能的脚本

验证TaskManager启动和日志系统是否正常工作
"""

import sys
import os
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_logger():
    """测试日志系统"""
    print("=== 测试日志系统 ===")
    try:
        from utils.logger import get_logger

        logger = get_logger()
        logger.info("测试信息日志")
        logger.warning("测试警告日志")
        logger.error("测试错误日志")

        print("[OK] 日志系统测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 日志系统测试失败: {e}")
        return False

def test_task_manager():
    """测试TaskManager启动"""
    print("\n=== 测试TaskManager启动 ===")
    try:
        from core.task_manager import TaskManager
        from utils.config_manager import ConfigManager

        config_manager = ConfigManager()
        task_manager = TaskManager(funasr_recognizer=None, config_manager=config_manager)

        # 尝试启动
        task_manager.start()
        print(f"[OK] TaskManager 启动成功，运行状态: {task_manager.is_running}")

        # 等待一秒
        time.sleep(1)

        # 停止
        task_manager.stop()
        print(f"[OK] TaskManager 停止成功，运行状态: {task_manager.is_running}")

        return True
    except Exception as e:
        print(f"[ERROR] TaskManager 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_continuous_recorder():
    """测试连续录音器（不使用真实音频）"""
    print("\n=== 测试ContinuousAudioRecorder ===")
    try:
        from core.continuous_recorder import ContinuousAudioRecorder, RecorderConfig
        from core.task_manager import TaskManager
        from utils.config_manager import ConfigManager

        config_manager = ConfigManager()
        task_manager = TaskManager(funasr_recognizer=None, config_manager=config_manager)
        task_manager.start()

        recorder_config = RecorderConfig(
            sample_rate=16000,
            channels=1,
            chunk_size=1024,
            min_segment_duration=0.5,
            max_segment_duration=8.0,
            silence_timeout=1.5,
        )

        recorder = ContinuousAudioRecorder(
            audio_engine=None,  # 不使用真实音频引擎
            task_manager=task_manager,
            config=recorder_config
        )

        print("[OK] ContinuousAudioRecorder 创建成功")

        # 清理
        task_manager.stop()
        return True
    except Exception as e:
        print(f"[ERROR] ContinuousAudioRecorder 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试修复功能...\n")

    results = []
    results.append(test_logger())
    results.append(test_task_manager())
    results.append(test_continuous_recorder())

    passed = sum(results)
    total = len(results)

    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("[OK] 所有测试通过！修复成功。")
    else:
        print("[ERROR] 部分测试失败，需要进一步调试。")

    return passed == total

if __name__ == "__main__":
    main()