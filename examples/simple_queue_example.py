#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单集成示例：如何将SQLite队列集成到现有系统
"""

from typing import Dict, Any
from .sqlite_task_queue import SQLiteTaskQueue, SQLiteTask, TaskType
import time
import uuid

class SimpleTaskProcessor:
    """简单任务处理器示例"""

    def __init__(self):
        self.queue = SQLiteTaskQueue("ququ_tasks.db")
        self.running = False

    def submit_recognition(self, audio_data: bytes, record_id: str) -> str:
        """提交语音识别任务"""
        task = SQLiteTask(
            task_id=str(uuid.uuid4()),
            task_type=TaskType.RECOGNITION.value,
            data={
                "audio_data": audio_data.hex(),  # 转为hex存储
                "record_id": record_id
            },
            priority=1
        )
        self.queue.put(task)
        return task.task_id

    def submit_correction(self, original_text: str, record_id: str) -> str:
        """提交文本修正任务"""
        task = SQLiteTask(
            task_id=str(uuid.uuid4()),
            task_type=TaskType.CORRECTION.value,
            data={
                "original_text": original_text,
                "record_id": record_id
            },
            priority=2
        )
        self.queue.put(task)
        return task.task_id

    def submit_translation(self, text: str, target_lang: str = "en", record_id: str = None) -> str:
        """提交翻译任务"""
        task = SQLiteTask(
            task_id=str(uuid.uuid4()),
            task_type=TaskType.TRANSLATION.value,
            data={
                "text": text,
                "target_language": target_lang,
                "record_id": record_id
            },
            priority=3
        )
        self.queue.put(task)
        return task.task_id

    def start_processing(self):
        """开始处理任务"""
        self.running = True

        while self.running:
            # 处理识别任务
            self._process_task_type(TaskType.RECOGNITION.value, self._handle_recognition)

            # 处理修正任务
            self._process_task_type(TaskType.CORRECTION.value, self._handle_correction)

            # 处理翻译任务
            self._process_task_type(TaskType.TRANSLATION.value, self._handle_translation)

            time.sleep(0.1)  # 短暂休息

    def _process_task_type(self, task_type: str, handler):
        """处理特定类型的任务"""
        task = self.queue.get(task_type, timeout=0.1)
        if task:
            try:
                result = handler(task.data)
                self.queue.complete_task(task.task_id, result)
                print(f"[完成] {task_type}: {task.task_id}")
            except Exception as e:
                self.queue.fail_task(task.task_id, str(e))
                print(f"[失败] {task_type}: {task.task_id} - {e}")

    def _handle_recognition(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理语音识别"""
        # 模拟识别过程
        time.sleep(0.5)
        return {
            "text": "这是识别结果",
            "confidence": 0.95,
            "record_id": data.get("record_id")
        }

    def _handle_correction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理文本修正"""
        # 模拟修正过程
        time.sleep(1.0)
        original = data.get("original_text", "")
        return {
            "optimized_text": f"修正后的：{original}",
            "record_id": data.get("record_id")
        }

    def _handle_translation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理翻译"""
        # 模拟翻译过程
        time.sleep(0.8)
        text = data.get("text", "")
        target_lang = data.get("target_language", "en")
        return {
            "translated_text": f"Translated({target_lang}): {text}",
            "record_id": data.get("record_id")
        }

    def stop(self):
        """停止处理"""
        self.running = False

    def get_stats(self):
        """获取统计信息"""
        return self.queue.get_statistics()


# 使用示例
if __name__ == "__main__":
    processor = SimpleTaskProcessor()

    # 提交一些测试任务
    processor.submit_recognition(b"mock_audio_data", "record_001")
    processor.submit_correction("原始文本", "record_001")
    processor.submit_translation("要翻译的文本", "en", "record_001")

    print("提交任务完成，统计：", processor.get_stats())

    # 在实际应用中，处理会在后台线程中运行
    # processor.start_processing()