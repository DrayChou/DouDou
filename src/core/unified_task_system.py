#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一任务系统 - 解决AI任务阻塞和重复问题

每个语音识别会话创建一个主任务，包含以下状态：
1. PENDING - 待处理
2. RECOGNIZING - 语音识别中
3. RECOGNIZED - 识别完成
4. CORRECTING - AI修正中
5. CORRECTED - 修正完成
6. TRANSLATING - 翻译中
7. COMPLETED - 全部完成
8. FAILED - 失败
9. TIMEOUT - 超时
"""

import time
import uuid
import threading
import queue
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
from utils.logger import get_logger

logger = get_logger()


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"           # 待处理
    RECOGNIZING = "recognizing"   # 语音识别中
    RECOGNIZED = "recognized"     # 识别完成
    CORRECTING = "correcting"     # AI修正中
    CORRECTED = "corrected"       # 修正完成
    TRANSLATING = "translating"   # 翻译中
    COMPLETED = "completed"       # 全部完成
    FAILED = "failed"            # 失败
    TIMEOUT = "timeout"          # 超时


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 3
    NORMAL = 2
    HIGH = 1


@dataclass
class UnifiedTask:
    """统一的语音处理任务"""
    audio_segment: Any = None
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_text: str = ""
    recognized_text: str = ""
    corrected_text: str = ""
    translated_text: str = ""

    # 状态管理
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # 错误信息
    error: Optional[str] = None

    # 配置
    enable_correction: bool = True
    enable_translation: bool = True
    target_language: str = "en"

    # 回调记录ID（用于UI关联）
    record_id: Optional[str] = None

    # 超时设置（秒）
    recognition_timeout: int = 30
    correction_timeout: int = 30
    translation_timeout: int = 30

    # 结果
    recognition_result: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()
        self.updated_at = self.created_at

    def update_status(self, status: TaskStatus, error: Optional[str] = None):
        """更新任务状态"""
        self.status = status
        self.updated_at = time.time()
        if error:
            self.error = error
        logger.debug(f"任务 {self.task_id} 状态更新为: {status.value}")

    def is_timeout(self, stage: str) -> bool:
        """检查是否超时"""
        elapsed = time.time() - self.updated_at
        timeout_map = {
            "recognition": self.recognition_timeout,
            "correction": self.correction_timeout,
            "translation": self.translation_timeout
        }
        return elapsed > timeout_map.get(stage, 30)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "original_text": self.original_text,
            "recognized_text": self.recognized_text,
            "corrected_text": self.corrected_text,
            "translated_text": self.translated_text,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
            "record_id": self.record_id
        }


class UnifiedTaskSystem:
    """统一任务管理系统"""

    def __init__(self, funasr_recognizer=None, config_manager=None):
        # 核心组件
        self.funasr_recognizer = funasr_recognizer
        self.config_manager = config_manager

        # 任务管理
        self.active_tasks: Dict[str, UnifiedTask] = {}  # task_id -> task
        self.pending_tasks: queue.PriorityQueue = queue.PriorityQueue(maxsize=100)
        # 去重集合：按阶段分离，避免同一任务在修正后立即进入翻译时被误判为重复
        self.processing_texts_correction: set = set()
        self.processing_texts_translation: set = set()

        # 线程池（限制并发数）
        self.recognition_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="Recognition")
        self.ai_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="AI")  # 单线程处理AI任务

        # 任务处理器
        self.task_processors: Dict[str, Any] = {}
        self._initialize_processors()

        # 统计信息
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.timeout_tasks = 0

        # 控制标志
        self.is_running = False
        self.shutdown_event = threading.Event()

        # 回调函数
        self.on_recognition_complete: Optional[Callable[[UnifiedTask], None]] = None
        self.on_correction_complete: Optional[Callable[[UnifiedTask], None]] = None
        self.on_translation_complete: Optional[Callable[[UnifiedTask], None]] = None
        self.on_task_complete: Optional[Callable[[UnifiedTask], None]] = None

        # 工作线程
        self.worker_thread: Optional[threading.Thread] = None

        logger.info("UnifiedTaskSystem 初始化完成")

    def _initialize_processors(self):
        """初始化任务处理器"""
        try:
            from .task_processors import TaskProcessorRegistry

            for processor_type in TaskProcessorRegistry.get_available_processors():
                processor = TaskProcessorRegistry.get_processor(processor_type)
                if processor:
                    self.task_processors[processor_type] = processor
                    logger.info(f"已注册处理器: {processor_type}")
        except ImportError as e:
            logger.error(f"导入任务处理器失败: {e}")
            self.task_processors = {}

    def start(self):
        """启动任务系统"""
        if self.is_running:
            logger.warning("UnifiedTaskSystem 已经在运行")
            return

        self.is_running = True
        self.shutdown_event.clear()

        # 启动工作线程
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            name="TaskWorker",
            daemon=True
        )
        self.worker_thread.start()

        logger.info("UnifiedTaskSystem 已启动")

    def stop(self):
        """停止任务系统"""
        if not self.is_running:
            return

        logger.info("正在停止 UnifiedTaskSystem...")
        self.is_running = False
        self.shutdown_event.set()

        # 等待工作线程结束
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)

        # 关闭线程池
        self.recognition_executor.shutdown(wait=True)
        self.ai_executor.shutdown(wait=True)

        logger.info("UnifiedTaskSystem 已停止")

    def submit_task(self, audio_segment: Any, record_id: str = None,
                   enable_correction: bool = True, enable_translation: bool = True,
                   priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """
        提交新的语音处理任务

        Args:
            audio_segment: 音频片段
            record_id: UI记录ID
            enable_correction: 是否启用AI修正
            enable_translation: 是否启用翻译
            priority: 任务优先级

        Returns:
            task_id: 任务ID
        """
        task = UnifiedTask(
            audio_segment=audio_segment,
            record_id=record_id,
            enable_correction=enable_correction,
            enable_translation=enable_translation,
            priority=priority
        )

        # 添加到任务管理
        self.active_tasks[task.task_id] = task
        self.total_tasks += 1

        # 提交到队列
        priority_item = (task.priority.value, task.created_at, task.task_id)
        try:
            self.pending_tasks.put(priority_item, timeout=1)
            logger.info(f"提交任务: {task.task_id}")
        except queue.Full:
            logger.error("任务队列已满，丢弃任务")
            self.active_tasks.pop(task.task_id, None)
            return None

        return task.task_id

    def _worker_loop(self):
        """工作线程主循环"""
        logger.info("任务工作线程启动")

        while self.is_running and not self.shutdown_event.is_set():
            try:
                # 获取待处理任务
                priority, created_at, task_id = self.pending_tasks.get(timeout=1)
                task = self.active_tasks.get(task_id)

                if not task:
                    continue

                # 处理任务
                self._process_task(task)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"工作线程异常: {e}")
                continue

        logger.info("任务工作线程停止")

    def _process_task(self, task: UnifiedTask):
        """处理单个任务的完整生命周期"""
        try:
            # 1. 语音识别
            if not self._process_recognition(task):
                return

            # 2. AI修正（如果启用）
            if task.enable_correction and task.recognized_text:
                if not self._process_correction(task):
                    return

            # 3. 翻译（如果启用）
            if task.enable_translation and (task.corrected_text or task.recognized_text):
                if not self._process_translation(task):
                    return

            # 任务完成
            task.update_status(TaskStatus.COMPLETED)
            self.completed_tasks += 1

            if self.on_task_complete:
                self.on_task_complete(task)

            logger.info(f"任务完成: {task.task_id}")

        except Exception as e:
            logger.error(f"处理任务 {task.task_id} 失败: {e}")
            task.update_status(TaskStatus.FAILED, str(e))
            self.failed_tasks += 1
        finally:
            # 清理
            self.active_tasks.pop(task.task_id, None)
            # 从去重集合中移除
            self.processing_texts_correction.discard(task.recognized_text)
            self.processing_texts_correction.discard(task.original_text)
            if getattr(task, 'corrected_text', None):
                self.processing_texts_correction.discard(task.corrected_text)
            # 翻译阶段的去重清理
            self.processing_texts_translation.discard(getattr(task, 'corrected_text', None) or task.recognized_text)

    def _process_recognition(self, task: UnifiedTask) -> bool:
        """处理语音识别"""
        task.update_status(TaskStatus.RECOGNIZING)

        try:
            future = self.recognition_executor.submit(self._do_recognition, task)

            # 等待结果，带超时
            result = future.result(timeout=task.recognition_timeout)

            task.recognition_result = result
            if result.get('success') and result.get('text'):
                task.recognized_text = result['text']
                # 将识别文本也记录在 original_text，便于处理器期望字段
                task.original_text = task.recognized_text
                task.update_status(TaskStatus.RECOGNIZED)

                if self.on_recognition_complete:
                    self.on_recognition_complete(task)

                return True
            else:
                task.update_status(TaskStatus.FAILED, "识别失败")
                return False

        except TimeoutError:
            logger.error(f"识别任务超时: {task.task_id}")
            task.update_status(TaskStatus.TIMEOUT, "识别超时")
            self.timeout_tasks += 1
            return False
        except Exception as e:
            logger.error(f"识别任务异常: {e}")
            task.update_status(TaskStatus.FAILED, str(e))
            return False

    def _process_correction(self, task: UnifiedTask) -> bool:
        """处理AI修正"""
        # 检查去重（修正阶段）
        if task.recognized_text in self.processing_texts_correction:
            logger.info(f"文本正在处理中，跳过修正: {task.recognized_text[:20]}...")
            return True

        self.processing_texts_correction.add(task.recognized_text)
        task.update_status(TaskStatus.CORRECTING)

        try:
            future = self.ai_executor.submit(self._do_correction, task)

            # 等待结果，带超时
            result = future.result(timeout=task.correction_timeout)

            # 处理器统一返回 {success: bool, result: str, error?: str}
            if result.get('success') and result.get('result'):
                task.corrected_text = result['result']
                task.update_status(TaskStatus.CORRECTED)

                if self.on_correction_complete:
                    self.on_correction_complete(task)

                return True
            else:
                logger.warning(f"修正任务失败，使用原文: {task.task_id}")
                task.corrected_text = task.recognized_text
                task.update_status(TaskStatus.CORRECTED)
                # 即使失败也回调，让UI能展示一条“修正”结果（等同原文）
                if self.on_correction_complete:
                    self.on_correction_complete(task)
                return True

        except TimeoutError:
            logger.error(f"修正任务超时: {task.task_id}")
            task.update_status(TaskStatus.TIMEOUT, "修正超时")
            self.timeout_tasks += 1
            # 超时也继续，使用原文
            task.corrected_text = task.recognized_text
            task.update_status(TaskStatus.CORRECTED)
            if self.on_correction_complete:
                self.on_correction_complete(task)
            return True
        except Exception as e:
            logger.error(f"修正任务异常: {e}")
            task.update_status(TaskStatus.FAILED, str(e))
            # 失败也继续，使用原文
            task.corrected_text = task.recognized_text
            task.update_status(TaskStatus.CORRECTED)
            if self.on_correction_complete:
                self.on_correction_complete(task)
            return True

    def _process_translation(self, task: UnifiedTask) -> bool:
        """处理翻译"""
        # 确定要翻译的文本
        source_text = task.corrected_text or task.recognized_text

        # 检查去重（翻译阶段）
        if source_text in self.processing_texts_translation:
            logger.info(f"文本正在处理中，跳过翻译: {source_text[:20]}...")
            return True

        self.processing_texts_translation.add(source_text)
        task.update_status(TaskStatus.TRANSLATING)

        try:
            # 获取翻译配置
            translation_config = self.config_manager.get_ai_service_config("translation")
            target_language = translation_config.get("target_language", task.target_language)
            # 将目标语言写回任务，供后续UI使用
            task.target_language = target_language

            future = self.ai_executor.submit(self._do_translation, task, source_text, target_language)

            # 等待结果，带超时
            result = future.result(timeout=task.translation_timeout)

            # 处理器统一返回 {success: bool, result: str, error?: str}
            if result.get('success') and result.get('result'):
                task.translated_text = result['result']

                if self.on_translation_complete:
                    self.on_translation_complete(task)

                return True
            else:
                logger.warning(f"翻译任务失败: {task.task_id}")
                # 失败也回调UI，给出提示信息
                err = result.get('error', '未知错误') if isinstance(result, dict) else '未知错误'
                task.translated_text = f"[提示: 翻译失败 - {err}]"
                if self.on_translation_complete:
                    self.on_translation_complete(task)
                return True

        except TimeoutError:
            logger.error(f"翻译任务超时: {task.task_id}")
            task.update_status(TaskStatus.TIMEOUT, "翻译超时")
            self.timeout_tasks += 1
            # 超时也回调UI
            task.translated_text = "[提示: 翻译超时]"
            if self.on_translation_complete:
                self.on_translation_complete(task)
            return True
        except Exception as e:
            logger.error(f"翻译任务异常: {e}")
            task.update_status(TaskStatus.FAILED, str(e))
            # 异常也回调UI
            task.translated_text = f"[提示: 翻译异常 - {str(e)}]"
            if self.on_translation_complete:
                self.on_translation_complete(task)
            return True

    def _do_recognition(self, task: UnifiedTask) -> Dict[str, Any]:
        """执行语音识别"""
        try:
            if self.funasr_recognizer:
                # 使用FunASR进行识别 - 兼容原有AudioSegment接口
                # 记录调试信息
                logger.debug(f"AudioSegment类型: {type(task.audio_segment)}")
                logger.debug(f"AudioSegment属性: {dir(task.audio_segment)}")
                logger.debug(f"hasattr file_path: {hasattr(task.audio_segment, 'file_path')}")

                if hasattr(task.audio_segment, 'file_path') and task.audio_segment.file_path:
                    # 原始接口：使用文件路径
                    logger.info(f"使用文件路径进行识别: {task.audio_segment.file_path}")
                    result = self.funasr_recognizer.transcribe_audio(task.audio_segment.file_path)
                    return {
                        'success': True,
                        'text': result.get('text', ''),
                        'confidence': result.get('confidence', 0.0),
                        'duration': task.audio_segment.duration
                    }
                else:
                    # 不支持的接口
                    logger.error(f"AudioSegment对象缺少file_path或file_path为空: {type(task.audio_segment)}")
                    logger.error(f"AudioSegment属性: {vars(task.audio_segment) if hasattr(task.audio_segment, '__dict__') else 'N/A'}")
                    return {
                        'success': False,
                        'text': '[AudioSegment缺少file_path]',
                        'confidence': 0.0,
                        'duration': 0.0
                    }
            else:
                # 模拟识别
                return {
                    'success': False,
                    'text': '[未配置识别器]',
                    'confidence': 0.0,
                    'duration': 0.0
                }
        except Exception as e:
            import traceback
            logger.error(f"语音识别异常: {e}")
            logger.error(f"异常详情: {traceback.format_exc()}")
            return {
                'success': False,
                'text': f'[识别错误: {str(e)}]',
                'confidence': 0.0,
                'duration': 0.0
            }

    def _do_correction(self, task: UnifiedTask) -> Dict[str, Any]:
        """执行AI修正"""
        try:
            processor = self.task_processors.get("correction")
            if not processor:
                return {'success': False, 'error': '修正处理器未找到'}

            # 构造最小任务对象，满足处理器的属性访问
            class _CorrectionTaskShim:
                def __init__(self, original_text: str):
                    self.original_text = original_text
                    self.optimized_text = None

            shim = _CorrectionTaskShim(original_text=task.recognized_text)

            task_data = {
                'task': shim,
                'base_config': self.config_manager.get_all() if self.config_manager else {}
            }

            # 直接返回处理器结果，外层统一读取 result
            return processor.process(task_data)

        except Exception as e:
            logger.error(f"AI修正异常: {e}")
            return {'success': False, 'error': str(e)}

    def _do_translation(self, task: UnifiedTask, source_text: str, target_language: str) -> Dict[str, Any]:
        """执行翻译"""
        try:
            processor = self.task_processors.get("translation")
            if not processor:
                return {'success': False, 'error': '翻译处理器未找到'}

            # 构造最小任务对象，满足处理器的属性访问
            class _TranslationTaskShim:
                def __init__(self, original_text: str, source_language: str, target_language: str):
                    self.original_text = original_text
                    self.source_language = source_language
                    self.target_language = target_language
                    self.translated_text = None

            shim = _TranslationTaskShim(
                original_text=source_text,
                source_language='zh',
                target_language=target_language,
            )

            task_data = {
                'task': shim,
                'base_config': self.config_manager.get_all() if self.config_manager else {}
            }

            # 直接返回处理器结果，外层统一读取 result
            return processor.process(task_data)

        except Exception as e:
            logger.error(f"翻译异常: {e}")
            return {'success': False, 'error': str(e)}

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.active_tasks.get(task_id)
        return task.to_dict() if task else None

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'timeout_tasks': self.timeout_tasks,
            'active_tasks': len(self.active_tasks),
            'pending_queue_size': self.pending_tasks.qsize(),
            # 分阶段统计 + 向后兼容的合计
            'processing_texts_correction': len(self.processing_texts_correction),
            'processing_texts_translation': len(self.processing_texts_translation),
            'processing_texts': len(self.processing_texts_correction) + len(self.processing_texts_translation)
        }

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.active_tasks.get(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RECOGNIZING]:
            task.update_status(TaskStatus.FAILED, "用户取消")
            self.active_tasks.pop(task_id, None)
            logger.info(f"任务已取消: {task_id}")
            return True
        return False

    def clear_pending_tasks(self):
        """清空待处理任务队列"""
        while not self.pending_tasks.empty():
            try:
                self.pending_tasks.get_nowait()
            except queue.Empty:
                break
        logger.info("已清空待处理任务队列")
