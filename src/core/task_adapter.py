#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务系统适配器 - 将新的UnifiedTaskSystem适配到现有的QuQu应用中

提供与原TaskManager相同的接口，确保无缝替换
"""

import time
from typing import Dict, Any, Optional, Callable
from .unified_task_system import UnifiedTaskSystem, UnifiedTask, TaskStatus, TaskPriority
from .task_manager import RecognitionTask, AIOptimizationTask, TranslationTask, TaskStatistics
from utils.logger import get_logger

logger = get_logger()


class TaskManagerAdapter:
    """任务管理器适配器 - 兼容原有接口"""

    def __init__(self, funasr_recognizer=None, config_manager=None):
        # 使用新的统一任务系统
        self.unified_system = UnifiedTaskSystem(
            funasr_recognizer=funasr_recognizer,
            config_manager=config_manager
        )

        # 为了兼容性，保留原有属性
        self.is_running = False
        self.config_manager = config_manager

        # 回调适配
        self.on_audio_segment: Optional[Callable] = None
        self.on_recognition_complete: Optional[Callable] = None
        self.on_correction_complete: Optional[Callable] = None
        self.on_translation_complete: Optional[Callable] = None
        self.on_ui_update: Optional[Callable] = None
        self.on_statistics_update: Optional[Callable] = None

        # 设置统一系统的回调
        self._setup_callbacks()

    def _setup_callbacks(self):
        """设置回调适配"""
        self.unified_system.on_recognition_complete = self._on_recognition_complete_adapter
        self.unified_system.on_correction_complete = self._on_correction_complete_adapter
        self.unified_system.on_translation_complete = self._on_translation_complete_adapter
        self.unified_system.on_task_complete = self._on_task_complete_adapter

    def _on_recognition_complete_adapter(self, unified_task: UnifiedTask):
        """识别完成回调适配器"""
        if self.on_recognition_complete:
            # 创建兼容的RecognitionTask对象
            recognition_task = RecognitionTask(
                audio_segment=unified_task.audio_segment,
                task_id=unified_task.task_id,
                created_at=unified_task.created_at,
                record_id=unified_task.record_id
            )
            recognition_task.result = unified_task.recognition_result
            self.on_recognition_complete(recognition_task)

    def _on_correction_complete_adapter(self, unified_task: UnifiedTask):
        """修正完成回调适配器"""
        if self.on_correction_complete:
            # 创建兼容的AIOptimizationTask对象
            correction_task = AIOptimizationTask(
                original_text=unified_task.recognized_text,
                recognition_result=unified_task.recognition_result,
                task_id=unified_task.task_id,
                created_at=unified_task.created_at,
                record_id=unified_task.record_id,
                optimized_text=unified_task.corrected_text
            )
            self.on_correction_complete(correction_task)

    def _on_translation_complete_adapter(self, unified_task: UnifiedTask):
        """翻译完成回调适配器"""
        if self.on_translation_complete:
            # 创建兼容的TranslationTask对象
            # 优先使用任务中的目标语言，其次读取配置
            target_lang = getattr(unified_task, 'target_language', None)
            if not target_lang and self.config_manager:
                cfg = self.config_manager.get_ai_service_config("translation")
                target_lang = cfg.get("target_language", "en")
            if not target_lang:
                target_lang = "en"

            translation_task = TranslationTask(
                original_text=unified_task.corrected_text or unified_task.recognized_text,
                source_language="zh",
                target_language=target_lang,
                task_id=unified_task.task_id,
                created_at=unified_task.created_at,
                record_id=unified_task.record_id,
                translated_text=unified_task.translated_text
            )
            self.on_translation_complete(translation_task)

    def _on_task_complete_adapter(self, unified_task: UnifiedTask):
        """任务完成回调适配器"""
        # 可以在这里添加UI更新或其他全局处理
        logger.debug(f"任务 {unified_task.task_id} 完整流程完成")

    def start(self):
        """启动任务管理器"""
        import time
        self._start_time = time.time()
        self.unified_system.start()
        self.is_running = True
        logger.info("TaskManagerAdapter 已启动")

    def stop(self):
        """停止任务管理器"""
        self.unified_system.stop()
        self.is_running = False
        logger.info("TaskManagerAdapter 已停止")

    def submit_recognition_task(self, recognition_task: RecognitionTask):
        """提交识别任务（兼容接口）"""
        return self.unified_system.submit_task(
            audio_segment=recognition_task.audio_segment,
            record_id=getattr(recognition_task, 'record_id', None),
            enable_correction=self.config_manager.get("enable_ai_optimization", False) if self.config_manager else False,
            enable_translation=self.config_manager.get("enable_translation", False) if self.config_manager else False,
            priority=TaskPriority.NORMAL
        )

    def submit_correction_task(self, correction_task: AIOptimizationTask):
        """提交修正任务（兼容接口）"""
        # 在新系统中，修正任务会自动跟随识别任务，这个方法主要用于兼容
        logger.warning("使用新系统时，修正任务会自动跟随识别任务，无需手动提交")
        return None

    def submit_task(self, audio_segment: Any = None, record_id: str = None,
                   enable_correction: bool = True, enable_translation: bool = True,
                   priority = None) -> str:
        """提交统一任务（兼容接口）"""
        from .unified_task_system import TaskPriority
        if priority is None:
            priority = TaskPriority.NORMAL
        return self.unified_system.submit_task(
            audio_segment=audio_segment,
            record_id=record_id,
            enable_correction=enable_correction,
            enable_translation=enable_translation,
            priority=priority
        )

    def submit_audio_segment(self, audio_segment) -> 'Future':
        """提交音频片段（兼容接口）"""
        # 创建模拟的Future对象以兼容原有接口
        from concurrent.futures import Future
        future = Future()

        try:
            # 转换为统一任务提交
            task_id = self.unified_system.submit_task(
                audio_segment=audio_segment,
                record_id=f"audio_{int(time.time() * 1000)}",
                enable_correction=self.config_manager.get("enable_ai_optimization", False) if self.config_manager else False,
                enable_translation=self.config_manager.get("enable_translation", False) if self.config_manager else False
            )
            # 设置结果为任务ID
            future.set_result(task_id)
        except Exception as e:
            future.set_exception(e)

        return future

    def submit_translation_task(self, translation_task: TranslationTask):
        """提交翻译任务（兼容接口）"""
        # 在新系统中，翻译任务会自动跟随识别/修正任务，这个方法主要用于兼容
        logger.warning("使用新系统时，翻译任务会自动跟随识别/修正任务，无需手动提交")
        return None

    def submit_ai_optimization_task(self, ai_task: AIOptimizationTask):
        """提交AI优化任务（兼容接口，映射到修正任务）"""
        return self.submit_correction_task(ai_task)

    def get_statistics(self):
        """获取统计信息"""
        stats = self.unified_system.get_statistics()
        # 返回TaskStatistics对象以兼容原有接口
        task_stats = TaskStatistics()
        task_stats.audio_completed = stats.get('completed_tasks', 0)
        task_stats.audio_failed = stats.get('failed_tasks', 0)
        task_stats.recognition_completed = stats.get('completed_tasks', 0)
        task_stats.recognition_failed = stats.get('failed_tasks', 0)
        task_stats.correction_completed = stats.get('completed_tasks', 0)
        task_stats.correction_failed = stats.get('failed_tasks', 0)
        task_stats.translation_completed = stats.get('completed_tasks', 0)
        task_stats.translation_failed = stats.get('failed_tasks', 0)
        task_stats.total_processed = stats.get('completed_tasks', 0)
        task_stats.total_failed = stats.get('failed_tasks', 0)
        # 设置启动时间以支持uptime计算
        import time
        task_stats.start_time = time.time() - getattr(self, '_start_time', 0)
        return task_stats

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        return self.unified_system.cancel_task(task_id)

    def clear_pending_tasks(self):
        """清空待处理任务"""
        self.unified_system.clear_pending_tasks()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        return self.unified_system.get_task_status(task_id)

    def _submit_ui_update(self, update_data: Dict[str, Any]):
        """提交UI更新任务（兼容接口）"""
        # UnifiedTaskSystem通过回调直接更新UI，不需要队列
        # 这个方法保留用于兼容性，但实际不执行任何操作
        pass

    # --- 新增：将识别阶段生成的 UI record_id 绑定回统一任务，便于后续修正/翻译关联 ---
    def bind_record_id(self, task_id: str, record_id: str) -> bool:
        try:
            task = self.unified_system.active_tasks.get(task_id)
            if task:
                task.record_id = record_id
                return True
            return False
        except Exception:
            return False


# 为了向后兼容，TaskStatistics 类从 task_manager 模块导入


# 创建工厂函数以便轻松切换系统
def create_task_manager(use_unified_system: bool = True, **kwargs):
    """创建任务管理器"""
    if use_unified_system:
        logger.info("使用新的统一任务系统")
        return TaskManagerAdapter(**kwargs)
    else:
        logger.info("使用原有的任务管理器")
        from .task_manager import TaskManager
        return TaskManager(**kwargs)
