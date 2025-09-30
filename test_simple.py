#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")

    try:
        from core.recognition_pipeline import RecognitionPipeline
        print("OK RecognitionPipeline 导入成功")
    except Exception as e:
        print(f"ERROR RecognitionPipeline 导入失败: {e}")
        return False

    try:
        from core.direct_funasr import DirectFunASR
        print("OK DirectFunASR 导入成功")
    except Exception as e:
        print(f"ERROR DirectFunASR 导入失败: {e}")
        return False

    try:
        from ui.components import RecordButton, ResultCard
        print("OK UI组件导入成功")
    except Exception as e:
        print(f"ERROR UI组件导入失败: {e}")
        return False

    return True

def test_pipeline_creation():
    """测试流水线创建"""
    print("测试流水线创建...")

    try:
        from core.recognition_pipeline import RecognitionPipeline
        pipeline = RecognitionPipeline(use_direct_integration=True)
        print("OK 识别流水线创建成功")
        return True
    except Exception as e:
        print(f"ERROR 识别流水线创建失败: {e}")
        return False

def test_ui_components():
    """测试UI组件创建"""
    print("测试UI组件创建...")

    try:
        from ui.components import RecordButton, ResultCard

        def dummy_callback():
            pass

        record_button = RecordButton(on_click=dummy_callback)
        print("OK 录音按钮创建成功")

        result_card = ResultCard()
        print("OK 结果卡片创建成功")

        return True
    except Exception as e:
        print(f"ERROR UI组件创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始功能测试...\n")

    tests = [
        test_imports,
        test_pipeline_creation,
        test_ui_components,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"ERROR 测试异常: {e}\n")

    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("SUCCESS 所有测试通过！")
        return True
    else:
        print("WARNING 部分测试失败")
        return False

if __name__ == "__main__":
    main()