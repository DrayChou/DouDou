#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器 - 多线程异步任务调度核心

协调录音、识别、AI优化等多个线程池的工作
"""

import asyncio
import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
import logging

# 使用统一日志系统
try:
    from utils.logger import get_logger
    logger = get_logger()
except ImportError:
    logger = logging.getLogger(__name__)



class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AudioSegment:
    """音频片段数据"""
    file_path: str
    timestamp: float
    duration: float
    segment_id: str
    vad_confidence: float
    sample_rate: int = 16000
    channels: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.segment_id:
            self.segment_id = str(uuid.uuid4())


@dataclass
class RecognitionTask:
    """语音识别任务"""
    audio_segment: AudioSegment
    task_id: str
    created_at: float
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    future: Optional[Future] = None
    record_id: Optional[str] = None  # 用于关联UI记录

    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()


@dataclass
class AIOptimizationTask:
    """AI优化任务（保持向后兼容）"""
    original_text: str
    recognition_result: Dict[str, Any]
    task_id: str
    created_at: float
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    optimized_text: Optional[str] = None
    error: Optional[str] = None
    future: Optional[Future] = None
    record_id: Optional[str] = None  # 用于关联识别记录

    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()


@dataclass
class TranslationTask:
    """翻译任务"""
    original_text: str
    source_language: str = "zh"
    target_language: str = "en"
    task_id: str = ""
    created_at: float = 0.0
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    translated_text: Optional[str] = None
    error: Optional[str] = None
    future: Optional[Future] = None
    context_history: Optional[List[str]] = None
    record_id: Optional[str] = None  # 用于关联识别记录

    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()


@dataclass
class TaskStatistics:
    """任务统计信息"""
    audio_pending: int = 0
    audio_processing: int = 0
    audio_completed: int = 0
    audio_failed: int = 0

    recognition_pending: int = 0
    recognition_processing: int = 0
    recognition_completed: int = 0
    recognition_failed: int = 0

    correction_pending: int = 0  # 重命名ai_pending为correction_pending
    correction_processing: int = 0
    correction_completed: int = 0
    correction_failed: int = 0

    translation_pending: int = 0
    translation_processing: int = 0
    translation_completed: int = 0
    translation_failed: int = 0

    total_processed: int = 0
    total_failed: int = 0
    start_time: float = field(default_factory=time.time)

    # 向后兼容的属性
    @property
    def ai_pending(self) -> int:
        """向后兼容：返回correction_pending"""
        return self.correction_pending

    @property
    def ai_processing(self) -> int:
        """向后兼容：返回correction_processing"""
        return self.correction_processing

    @property
    def ai_completed(self) -> int:
        """向后兼容：返回correction_completed"""
        return self.correction_completed

    @property
    def ai_failed(self) -> int:
        """向后兼容：返回correction_failed"""
        return self.correction_failed

    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.total_processed + self.total_failed
        if total == 0:
            return 0.0
        return self.total_processed / total

    @property
    def uptime(self) -> float:
        """运行时间（秒）"""
        return time.time() - self.start_time


class TaskManager:
    """任务管理器 - 协调各个线程池的工作"""

    def __init__(self, funasr_recognizer=None, config_manager=None):
        # 任务队列
        self.audio_queue = queue.PriorityQueue(maxsize=100)
        self.recognition_queue = queue.PriorityQueue(maxsize=50)
        self.correction_queue = queue.PriorityQueue(maxsize=50)  # 重命名ai_optimization_queue
        self.translation_queue = queue.PriorityQueue(maxsize=50)  # 新增翻译队列
        self.ui_update_queue = queue.Queue(maxsize=100)

        # 线程池
        self.audio_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="Audio")
        self.recognition_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="Recognition")
        self.correction_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="Correction")  # 重命名ai_pool
        self.translation_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="Translation")  # 新增翻译线程池

        # FunASR识别器
        self.funasr_recognizer = funasr_recognizer

        # 配置管理器
        self.config_manager = config_manager

        # 任务处理器注册和实例化
        self.task_processors: Dict[str, Any] = {}
        self._initialize_processors()

        # 任务跟踪
        self.active_tasks: Dict[str, Any] = {}  # task_id -> task
        self.task_futures: Dict[str, Future] = {}  # task_id -> future

        # 统计信息
        self.statistics = TaskStatistics()
        self.stats_lock = threading.Lock()

        # 控制标志
        self.is_running = False
        self.shutdown_event = threading.Event()

        # 回调函数
        self.on_audio_segment: Optional[Callable[[AudioSegment], None]] = None
        self.on_recognition_complete: Optional[Callable[[RecognitionTask], None]] = None
        self.on_correction_complete: Optional[Callable[[AIOptimizationTask], None]] = None  # 重命名ai_optimization_complete
        self.on_translation_complete: Optional[Callable[[TranslationTask], None]] = None  # 新增翻译完成回调
        self.on_ui_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_statistics_update: Optional[Callable[[TaskStatistics], None]] = None

        # UI更新线程
        self.ui_update_thread: Optional[threading.Thread] = None

        logger.info("TaskManager 初始化完成")

    def _initialize_processors(self):
        """初始化任务处理器"""
        try:
            from .task_processors import TaskProcessorRegistry

            # 注册所有处理器（通过装饰器自动注册的）
            # 获取处理器实例
            for processor_type in TaskProcessorRegistry.get_available_processors():
                processor = TaskProcessorRegistry.get_processor(processor_type)
                if processor:
                    self.task_processors[processor_type] = processor
                    logger.info(f"TaskManager: 已注册处理器 {processor_type}")
                else:
                    logger.warning(f"TaskManager: 无法获取处理器实例 {processor_type}")

        except ImportError as e:
            logger.error(f"TaskManager: 导入任务处理器失败: {e}")
            # 创建一个空的处理器字典，避免后续调用出错
            self.task_processors = {}

    def start(self):
        """启动任务管理器"""
        if self.is_running:
            logger.warning("TaskManager 已经在运行")
            return

        self.is_running = True
        self.shutdown_event.clear()

        # 启动UI更新线程
        self.ui_update_thread = threading.Thread(
            target=self._ui_update_worker,
            name="UI-Update",
            daemon=True
        )
        self.ui_update_thread.start()

        logger.info("TaskManager 已启动")

    def stop(self):
        """停止任务管理器"""
        if not self.is_running:
            return

        logger.info("正在停止 TaskManager...")
        self.is_running = False
        self.shutdown_event.set()

        # 取消所有活动任务
        for task_id, future in self.task_futures.items():
            if not future.done():
                future.cancel()
                self._update_task_status(task_id, TaskStatus.CANCELLED)

        # 关闭线程池
        self.audio_pool.shutdown(wait=True)
        self.recognition_pool.shutdown(wait=True)
        self.correction_pool.shutdown(wait=True)
        self.translation_pool.shutdown(wait=True)

        # 等待UI更新线程结束
        if self.ui_update_thread and self.ui_update_thread.is_alive():
            self.ui_update_thread.join(timeout=2.0)

        logger.info("TaskManager 已停止")

    def submit_audio_segment(self, audio_segment: AudioSegment) -> Future:
        """提交音频片段任务"""
        if not self.is_running:
            raise RuntimeError("TaskManager 未启动")

        # 更新统计
        with self.stats_lock:
            self.statistics.audio_pending += 1

        # 创建任务并提交到音频队列
        task = RecognitionTask(
            audio_segment=audio_segment,
            task_id=str(uuid.uuid4()),
            created_at=time.time()
        )

        # 使用优先级队列：(priority, timestamp, task)
        priority_value = -task.priority.value  # 负数实现高优先级在前
        queue_item = (priority_value, time.time(), task)

        self.active_tasks[task.task_id] = task
        self.audio_queue.put(queue_item)

        # 提交到线程池处理
        future = self.audio_pool.submit(self._process_audio_segment, task)
        task.future = future
        self.task_futures[task.task_id] = future

        logger.info(f"提交音频片段任务: {task.task_id}, 文件: {audio_segment.file_path}")
        return future

    def submit_recognition_task(self, recognition_task: RecognitionTask) -> Future:
        """提交语音识别任务"""
        if not self.is_running:
            raise RuntimeError("TaskManager 未启动")

        with self.stats_lock:
            self.statistics.recognition_pending += 1

        priority_value = -recognition_task.priority.value
        queue_item = (priority_value, time.time(), recognition_task)

        self.active_tasks[recognition_task.task_id] = recognition_task
        self.recognition_queue.put(queue_item)

        future = self.recognition_pool.submit(self._process_recognition_task, recognition_task)
        recognition_task.future = future
        self.task_futures[recognition_task.task_id] = future

        logger.info(f"提交识别任务: {recognition_task.task_id}")
        return future

    def submit_ai_optimization_task(self, ai_task: AIOptimizationTask) -> Future:
        """提交AI优化任务（重命名为correction）"""
        return self.submit_correction_task(ai_task)

    def submit_correction_task(self, correction_task: AIOptimizationTask) -> Future:
        """提交文本修正任务"""
        if not self.is_running:
            raise RuntimeError("TaskManager 未启动")

        with self.stats_lock:
            self.statistics.correction_pending += 1

        priority_value = -correction_task.priority.value
        queue_item = (priority_value, time.time(), correction_task)

        self.active_tasks[correction_task.task_id] = correction_task
        self.correction_queue.put(queue_item)

        future = self.correction_pool.submit(self._process_generic_task, correction_task, "correction")
        correction_task.future = future
        self.task_futures[correction_task.task_id] = future

        logger.info(f"提交文本修正任务: {correction_task.task_id}")
        return future

    def submit_translation_task(self, translation_task: TranslationTask) -> Future:
        """提交翻译任务"""
        if not self.is_running:
            raise RuntimeError("TaskManager 未启动")

        # 检查翻译功能是否启用
        if self.config_manager and not self.config_manager.get('enable_translation', False):
            raise RuntimeError("翻译功能未启用")

        with self.stats_lock:
            self.statistics.translation_pending += 1

        priority_value = -translation_task.priority.value
        queue_item = (priority_value, time.time(), translation_task)

        self.active_tasks[translation_task.task_id] = translation_task
        self.translation_queue.put(queue_item)

        future = self.translation_pool.submit(self._process_generic_task, translation_task, "translation")
        translation_task.future = future
        self.task_futures[translation_task.task_id] = future

        logger.info(f"提交翻译任务: {translation_task.task_id}")
        return future

    def _process_audio_segment(self, task: RecognitionTask) -> Dict[str, Any]:
        """处理音频片段（在音频线程池中执行）"""
        try:
            self._update_task_status(task.task_id, TaskStatus.PROCESSING)
            with self.stats_lock:
                self.statistics.audio_processing += 1
                self.statistics.audio_pending -= 1

            # 调用回调处理音频片段
            if self.on_audio_segment:
                self.on_audio_segment(task.audio_segment)

            # 音频处理完成后，自动提交到识别队列
            self.submit_recognition_task(task)

            result = {
                'task_id': task.task_id,
                'status': 'processed',
                'audio_segment': task.audio_segment
            }

            self._update_task_status(task.task_id, TaskStatus.COMPLETED)
            with self.stats_lock:
                self.statistics.audio_processing -= 1
                self.statistics.audio_completed += 1
                self.statistics.total_processed += 1

            return result

        except Exception as e:
            logger.error(f"处理音频片段失败: {e}")
            self._update_task_status(task.task_id, TaskStatus.FAILED, str(e))
            with self.stats_lock:
                self.statistics.audio_processing -= 1
                self.statistics.audio_failed += 1
                self.statistics.total_failed += 1
            return {'task_id': task.task_id, 'status': 'failed', 'error': str(e)}

    def _process_recognition_task(self, task: RecognitionTask) -> Dict[str, Any]:
        """处理语音识别任务（在识别线程池中执行）"""
        try:
            self._update_task_status(task.task_id, TaskStatus.PROCESSING)
            with self.stats_lock:
                self.statistics.recognition_processing += 1
                self.statistics.recognition_pending -= 1

            # 使用真实的FunASR识别
            if self.funasr_recognizer:
                try:
                    funasr_result = self.funasr_recognizer.transcribe_audio(task.audio_segment.file_path)
                    result = {
                        'success': funasr_result.get('success', False),
                        'text': funasr_result.get('text', ''),
                        'confidence': funasr_result.get('confidence', 0.0),
                        'duration': funasr_result.get('duration', task.audio_segment.duration)
                    }
                except Exception as e:
                    logger.error(f"FunASR识别失败: {e}")
                    result = {
                        'success': False,
                        'text': f'识别失败: {str(e)}',
                        'confidence': 0.0,
                        'duration': task.audio_segment.duration
                    }
            else:
                # 降级：没有识别器时返回提示
                result = {
                    'success': False,
                    'text': '[未配置识别器]',
                    'confidence': 0.0,
                    'duration': task.audio_segment.duration
                }

            task.result = result

            # 调用回调
            if self.on_recognition_complete:
                self.on_recognition_complete(task)

            # 识别成功后，如果启用AI优化，自动提交到AI优化队列
            if result.get('success') and result.get('text'):
                ai_task = AIOptimizationTask(
                    original_text=result['text'],
                    recognition_result=result,
                    task_id=str(uuid.uuid4()),
                    created_at=time.time(),
                    priority=task.priority
                )
                self.submit_ai_optimization_task(ai_task)

            self._update_task_status(task.task_id, TaskStatus.COMPLETED)
            with self.stats_lock:
                self.statistics.recognition_processing -= 1
                self.statistics.recognition_completed += 1
                self.statistics.total_processed += 1

            return {'task_id': task.task_id, 'status': 'completed', 'result': result}

        except Exception as e:
            logger.error(f"处理识别任务失败: {e}")
            self._update_task_status(task.task_id, TaskStatus.FAILED, str(e))
            with self.stats_lock:
                self.statistics.recognition_processing -= 1
                self.statistics.recognition_failed += 1
                self.statistics.total_failed += 1
            return {'task_id': task.task_id, 'status': 'failed', 'error': str(e)}

    def _process_ai_optimization_task(self, task: AIOptimizationTask) -> Dict[str, Any]:
        """处理AI优化任务（在AI线程池中执行）"""
        try:
            self._update_task_status(task.task_id, TaskStatus.PROCESSING)
            with self.stats_lock:
                self.statistics.ai_processing += 1
                self.statistics.ai_pending -= 1

            # 这里应该调用实际的AI优化服务
            # 暂时返回模拟结果
            time.sleep(0.2)  # 模拟AI优化耗时
            task.optimized_text = f"优化后: {task.original_text}"

            # 调用回调
            if self.on_ai_optimization_complete:
                self.on_ai_optimization_complete(task)

            # 提交UI更新
            self._submit_ui_update({
                'type': 'ai_optimization_complete',
                'task_id': task.task_id,
                'original_text': task.original_text,
                'optimized_text': task.optimized_text,
                'timestamp': time.time()
            })

            self._update_task_status(task.task_id, TaskStatus.COMPLETED)
            with self.stats_lock:
                self.statistics.ai_processing -= 1
                self.statistics.ai_completed += 1
                self.statistics.total_processed += 1

            return {
                'task_id': task.task_id,
                'status': 'completed',
                'optimized_text': task.optimized_text
            }

        except Exception as e:
            logger.error(f"处理AI优化任务失败: {e}")
            self._update_task_status(task.task_id, TaskStatus.FAILED, str(e))
            with self.stats_lock:
                self.statistics.ai_processing -= 1
                self.statistics.ai_failed += 1
                self.statistics.total_failed += 1
            return {'task_id': task.task_id, 'status': 'failed', 'error': str(e)}

    def _process_generic_task(self, task, task_type: str) -> Dict[str, Any]:
        """
        通用任务处理器（在对应的线程池中执行）

        Args:
            task: 任务对象（AIOptimizationTask 或 TranslationTask）
            task_type: 任务类型（'correction' 或 'translation'）

        Returns:
            Dict: 处理结果
        """
        logger.info(f"[DEBUG] 开始处理{task_type}任务: {task.task_id}")
        try:
            self._update_task_status(task.task_id, TaskStatus.PROCESSING)

            # 更新统计信息
            with self.stats_lock:
                if task_type == "correction":
                    self.statistics.correction_processing += 1
                    self.statistics.correction_pending -= 1
                elif task_type == "translation":
                    self.statistics.translation_processing += 1
                    self.statistics.translation_pending -= 1

            # 获取处理器
            processor = self.task_processors.get(task_type)
            if not processor:
                logger.error(f"[DEBUG] 未找到任务处理器: {task_type}, 可用处理器: {list(self.task_processors.keys())}")
                raise ValueError(f"未找到任务处理器: {task_type}")

            logger.info(f"[DEBUG] 找到处理器: {processor}, 准备构建任务数据")

            # 构建任务数据
            task_data = {
                'task': task,
                'base_config': self.config_manager.get_all() if self.config_manager else {}
            }

            logger.info(f"[DEBUG] 任务数据已构建，config_manager存在: {self.config_manager is not None}")

            # 如果是翻译任务，尝试添加上下文历史
            if task_type == "translation" and hasattr(task, 'context_history'):
                task_data['context_history'] = task.context_history

            # 调用处理器处理任务
            logger.info(f"[DEBUG] 开始调用处理器处理任务")
            result = processor.process(task_data)
            logger.info(f"[DEBUG] 处理器返回结果: success={result.get('success')}, error={result.get('error')}")

            if result.get("success"):
                # 更新任务结果
                if task_type == "correction" and hasattr(task, 'optimized_text'):
                    task.optimized_text = result.get("result")
                elif task_type == "translation" and hasattr(task, 'translated_text'):
                    task.translated_text = result.get("result")

                # 调用回调
                if task_type == "correction" and self.on_correction_complete:
                    logger.info(f"[DEBUG] 调用修正完成回调，task_id: {task.task_id}")
                    try:
                        self.on_correction_complete(task)
                        logger.info(f"[DEBUG] 修正完成回调执行成功")
                    except Exception as e:
                        logger.error(f"[DEBUG] 修正完成回调执行失败: {e}")
                elif task_type == "translation" and self.on_translation_complete:
                    logger.info(f"[DEBUG] 调用翻译完成回调，task_id: {task.task_id}")
                    try:
                        self.on_translation_complete(task)
                        logger.info(f"[DEBUG] 翻译完成回调执行成功")
                    except Exception as e:
                        logger.error(f"[DEBUG] 翻译完成回调执行失败: {e}")

                # 提交UI更新
                self._submit_ui_update({
                    'type': f'{task_type}_complete',
                    'task_id': task.task_id,
                    'original_text': task.original_text,
                    'result': result.get("result"),
                    'timestamp': time.time(),
                    **{k: v for k, v in result.items() if k not in ['success', 'result']}
                })

                self._update_task_status(task.task_id, TaskStatus.COMPLETED)
                with self.stats_lock:
                    if task_type == "correction":
                        self.statistics.correction_processing -= 1
                        self.statistics.correction_completed += 1
                    elif task_type == "translation":
                        self.statistics.translation_processing -= 1
                        self.statistics.translation_completed += 1
                    self.statistics.total_processed += 1

                return {
                    'task_id': task.task_id,
                    'status': 'completed',
                    'result': result.get("result"),
                    **{k: v for k, v in result.items() if k not in ['success', 'result']}
                }
            else:
                # 处理失败
                error_msg = result.get("error", "处理器返回失败")
                self._update_task_status(task.task_id, TaskStatus.FAILED, error_msg)
                with self.stats_lock:
                    if task_type == "correction":
                        self.statistics.correction_processing -= 1
                        self.statistics.correction_failed += 1
                    elif task_type == "translation":
                        self.statistics.translation_processing -= 1
                        self.statistics.translation_failed += 1
                    self.statistics.total_failed += 1

                return {'task_id': task.task_id, 'status': 'failed', 'error': error_msg}

        except Exception as e:
            logger.error(f"处理{task_type}任务失败: {e}")
            self._update_task_status(task.task_id, TaskStatus.FAILED, str(e))
            with self.stats_lock:
                if task_type == "correction":
                    self.statistics.correction_processing -= 1
                    self.statistics.correction_failed += 1
                elif task_type == "translation":
                    self.statistics.translation_processing -= 1
                    self.statistics.translation_failed += 1
                self.statistics.total_failed += 1
            return {'task_id': task.task_id, 'status': 'failed', 'error': str(e)}

    def _submit_ui_update(self, update_data: Dict[str, Any]):
        """提交UI更新任务"""
        try:
            self.ui_update_queue.put_nowait(update_data)
        except queue.Full:
            logger.warning("UI更新队列已满，丢弃更新")

    def _ui_update_worker(self):
        """UI更新工作线程"""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # 等待UI更新任务，超时0.1秒以便检查关闭事件
                update_data = self.ui_update_queue.get(timeout=0.1)

                # 调用UI更新回调
                if self.on_ui_update:
                    self.on_ui_update(update_data)

                # 通知统计更新
                if self.on_statistics_update:
                    self.on_statistics_update(self.statistics)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"UI更新处理失败: {e}")

    def _update_task_status(self, task_id: str, status: TaskStatus, error: Optional[str] = None):
        """更新任务状态"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = status
            if error:
                task.error = error

    def get_statistics(self) -> TaskStatistics:
        """获取统计信息"""
        with self.stats_lock:
            return TaskStatistics(**self.statistics.__dict__)

    def get_queue_status(self) -> Dict[str, int]:
        """获取队列状态"""
        return {
            'audio_queue_size': self.audio_queue.qsize(),
            'recognition_queue_size': self.recognition_queue.qsize(),
            'correction_queue_size': self.correction_queue.qsize(),
            'translation_queue_size': self.translation_queue.qsize(),
            'ui_update_queue_size': self.ui_update_queue.qsize(),
            # 向后兼容
            'ai_optimization_queue_size': self.correction_queue.qsize(),
        }

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.task_futures:
            future = self.task_futures[task_id]
            if future.cancel():
                self._update_task_status(task_id, TaskStatus.CANCELLED)
                logger.info(f"任务已取消: {task_id}")
                return True
        return False

    def clear_queues(self):
        """清空所有队列"""
        # 清空队列（丢弃所有待处理任务）
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        while not self.recognition_queue.empty():
            try:
                self.recognition_queue.get_nowait()
            except queue.Empty:
                break

        while not self.correction_queue.empty():
            try:
                self.correction_queue.get_nowait()
            except queue.Empty:
                break

        while not self.translation_queue.empty():
            try:
                self.translation_queue.get_nowait()
            except queue.Empty:
                break

        # 向后兼容：清空旧的ai_optimization_queue（如果还存在）
        if hasattr(self, 'ai_optimization_queue'):
            while not self.ai_optimization_queue.empty():
                try:
                    self.ai_optimization_queue.get_nowait()
                except queue.Empty:
                    break

        while not self.ui_update_queue.empty():
            try:
                self.ui_update_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("所有队列已清空")

    def __del__(self):
        """析构函数"""
        if self.is_running:
            self.stop()