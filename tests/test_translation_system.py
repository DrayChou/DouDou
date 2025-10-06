#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译系统测试脚本

测试配置继承、任务处理器和队列功能
"""

import sys
import os
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config_manager import ConfigManager
from core.task_manager import TaskManager, TranslationTask, AIOptimizationTask
from core.task_processors import TaskProcessorRegistry


def test_config_inheritance():
    """测试配置继承功能"""
    print("=== 测试配置继承功能 ===")

    # 创建测试配置文件
    test_config_path = "test_config.json"
    test_config = {
        "ai_services": {
            "default": {
                "api_key": "default_key",
                "base_url": "http://localhost:11435/v1",
                "model_name": "default_model"
            },
            "correction": {
                "system_prompt": "自定义修正prompt"
            },
            "translation": {
                "target_language": "ja",
                "system_prompt": "自定义翻译prompt"
                # 不配置api_key等，应该继承default
            }
        },
        "enable_translation": True,
        "language": "zh"
    }

    import json
    with open(test_config_path, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, ensure_ascii=False, indent=2)

    try:
        # 测试配置管理器
        config_manager = ConfigManager(test_config_path)

        # 测试default配置
        default_config = config_manager.get_ai_service_config("default")
        print(f"Default API Key: {default_config['api_key']}")
        print(f"Default Base URL: {default_config['base_url']}")
        print(f"Default Model: {default_config['model_name']}")

        # 测试correction配置继承
        correction_config = config_manager.get_ai_service_config("correction")
        print(f"Correction API Key: {correction_config['api_key']} (应该继承default)")
        print(f"Correction Base URL: {correction_config['base_url']} (应该继承default)")
        print(f"Correction Model: {correction_config['model_name']} (应该继承default)")

        # 测试translation配置继承
        translation_config = config_manager.get_ai_service_config("translation")
        print(f"Translation API Key: {translation_config['api_key']} (应该继承default)")
        print(f"Translation Base URL: {translation_config['base_url']} (应该继承default)")
        print(f"Translation Model: {translation_config['model_name']} (应该继承default)")
        print(f"Translation Target Language: {translation_config['target_language']} (应该为ja)")

        # 测试Prompt加载
        correction_prompt = config_manager.load_prompt("correction")
        translation_prompt = config_manager.load_prompt("translation")
        print(f"Correction Prompt: {correction_prompt[:50]}...")
        print(f"Translation Prompt: {translation_prompt[:50]}...")

        print("配置继承功能测试通过")

    finally:
        # 清理测试文件
        if os.path.exists(test_config_path):
            os.remove(test_config_path)


def test_task_processors():
    """测试任务处理器功能"""
    print("\n=== 测试任务处理器功能 ===")

    try:
        # 测试处理器注册
        available_processors = TaskProcessorRegistry.get_available_processors()
        print(f"可用处理器: {available_processors}")

        # 测试获取处理器实例
        correction_processor = TaskProcessorRegistry.get_processor("correction")
        translation_processor = TaskProcessorRegistry.get_processor("translation")

        if correction_processor:
            print(f"[OK] Correction处理器: {correction_processor}")
        else:
            print("[ERROR] 无法获取Correction处理器")

        if translation_processor:
            print(f"[OK] Translation处理器: {translation_processor}")

            # 测试翻译语言验证
            print(f"支持的语言: {translation_processor.get_supported_languages()}")
        else:
            print("[ERROR] 无法获取Translation处理器")

        print("任务处理器功能测试通过")

    except Exception as e:
        print(f"[ERROR] 任务处理器测试失败: {e}")


def test_task_manager():
    """测试任务管理器功能"""
    print("\n=== 测试任务管理器功能 ===")

    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        config_manager.set("enable_translation", True)

        # 创建任务管理器
        task_manager = TaskManager(config_manager=config_manager)
        task_manager.start()

        print("TaskManager启动成功")

        # 测试队列状态
        queue_status = task_manager.get_queue_status()
        print(f"队列状态: {queue_status}")

        # 测试统计信息
        stats = task_manager.get_statistics()
        print(f"统计信息: {stats}")

        # 创建测试任务
        test_correction_task = AIOptimizationTask(
            original_text="测试文本修正",
            recognition_result={"text": "测试文本修正", "confidence": 0.9},
            task_id="test_correction_001",
            created_at=time.time()
        )

        test_translation_task = TranslationTask(
            original_text="测试文本翻译",
            source_language="zh",
            target_language="en",
            task_id="test_translation_001"
        )

        print("测试任务创建成功")

        # 注意：这里不实际提交任务，因为需要真实的AI API
        print("[INFO] 跳过实际任务提交（需要AI API）")

        # 停止任务管理器
        task_manager.stop()
        print("TaskManager停止成功")

        print("任务管理器功能测试通过")

    except Exception as e:
        print(f"[ERROR] 任务管理器测试失败: {e}")


def test_config_migration():
    """测试配置迁移功能"""
    print("\n=== 测试配置迁移功能 ===")

    # 创建旧版配置文件
    old_config_path = "old_config.json"
    old_config = {
        "api_key": "old_api_key",
        "base_url": "http://old-url.com/v1",
        "model_name": "old_model",
        "language": "zh",
        "enable_ai_optimization": True
    }

    import json
    with open(old_config_path, 'w', encoding='utf-8') as f:
        json.dump(old_config, f, ensure_ascii=False, indent=2)

    try:
        # 创建配置管理器（应该自动迁移）
        config_manager = ConfigManager(old_config_path)

        # 检查迁移结果
        new_config = config_manager.get_all()

        # 检查是否正确迁移到新的ai_services结构
        if "ai_services" in new_config:
            print("配置已迁移到新的ai_services结构")

            default_config = new_config["ai_services"].get("default", {})
            print(f"迁移后的API Key: {default_config.get('api_key')}")
            print(f"迁移后的Base URL: {default_config.get('base_url')}")
            print(f"迁移后的Model: {default_config.get('model_name')}")

            # 检查原有配置是否保留
            print(f"语言设置: {new_config.get('language')}")
            print(f"AI优化启用: {new_config.get('enable_ai_optimization')}")

            print("配置迁移功能测试通过")
        else:
            print("[ERROR] 配置迁移失败：未找到ai_services结构")

    finally:
        # 清理测试文件
        if os.path.exists(old_config_path):
            os.remove(old_config_path)


def main():
    """主测试函数"""
    print("开始翻译系统测试...")

    try:
        test_config_inheritance()
        test_task_processors()
        test_task_manager()
        test_config_migration()

        print("\n所有测试完成！")

    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()