#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转写处理模块

处理音频转写、AI文本优化等功能
"""

import threading
from typing import Dict, Any, Optional, Callable

from .recognition_pipeline import RecognitionPipeline
from .ai_integration import AIProcessor


class TranscriptionHandler:
    """转写处理管理器"""

    def __init__(
        self,
        recognition_pipeline: RecognitionPipeline,
        ai_processor: Optional[AIProcessor] = None
    ):
        """
        初始化转写处理器

        Args:
            recognition_pipeline: 语音识别流水线
            ai_processor: AI处理器（可选）
        """
        self.pipeline = recognition_pipeline
        self.ai_processor = ai_processor
        self.transcription_result = ""
        self.is_processing = False

        # 回调函数
        self.on_transcription_complete: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_ai_optimization_complete: Optional[Callable[[str], None]] = None
        self.get_context_history: Optional[Callable[[], list]] = None  # 获取上下文历史的回调

    def transcribe_audio_file(
        self,
        audio_path: str,
        options: Optional[Dict[str, Any]] = None,
        enable_ai_optimization: bool = False
    ) -> None:
        """
        异步转写音频文件

        Args:
            audio_path: 音频文件路径
            options: 识别选项
            enable_ai_optimization: 是否启用AI优化
        """
        if self.is_processing:
            print("[TranscriptionHandler] 正在处理中，请稍候")
            return

        self.is_processing = True

        # 启动转写线程
        thread = threading.Thread(
            target=self._transcription_worker,
            args=(audio_path, options, enable_ai_optimization),
            daemon=True
        )
        thread.start()

    def _transcription_worker(
        self,
        audio_path: str,
        options: Optional[Dict[str, Any]],
        enable_ai_optimization: bool
    ):
        """转写工作线程"""
        try:
            self.update_status("正在转写音频...")

            # 执行语音识别
            result = self.pipeline.transcribe_audio(audio_path, options)

            if result.get("success"):
                raw_text = result.get("text", "")
                self.transcription_result = raw_text

                # 触发转写完成回调
                if self.on_transcription_complete:
                    self.on_transcription_complete(result)

                # AI优化
                if enable_ai_optimization and self.ai_processor and raw_text.strip():
                    # 获取上下文历史
                    context_history = self.get_context_history() if self.get_context_history else []
                    self._optimize_text_async(raw_text, context_history)
                else:
                    self.update_status("转写完成")

            else:
                error_msg = result.get("error", "未知错误")
                self.update_status(f"转写失败: {error_msg}")

                if self.on_transcription_complete:
                    self.on_transcription_complete(result)

        except Exception as e:
            print(f"[TranscriptionHandler] 转写异常: {e}")
            self.update_status(f"转写异常: {str(e)}")

        finally:
            self.is_processing = False

    def optimize_text_async(self, raw_text: str, context_history: Optional[list] = None):
        """异步AI文本优化"""
        self._optimize_text_async(raw_text, context_history)

    def _optimize_text_async(self, raw_text: str, context_history: Optional[list] = None):
        """异步AI文本优化（内部方法）"""
        thread = threading.Thread(
            target=self._ai_optimization_worker,
            args=(raw_text, context_history),
            daemon=True
        )
        thread.start()

    def _ai_optimization_worker(self, raw_text: str, context_history: Optional[list] = None):
        """AI优化工作线程"""
        try:
            self.update_status("AI正在优化文本...")

            result = self.ai_processor.optimize_text(raw_text, context_history)

            if result.get("success"):
                optimized_text = result.get("text", "").strip()

                if optimized_text and optimized_text != raw_text.strip():
                    self.transcription_result = optimized_text
                    self.update_status("AI优化完成")

                    # 触发AI优化完成回调
                    if self.on_ai_optimization_complete:
                        self.on_ai_optimization_complete(optimized_text)
                else:
                    self.update_status("文本无需优化")
            else:
                # AI优化失败，直接在结果区显示错误，不占用状态栏
                error_msg = result.get("error", "优化失败")
                if self.on_ai_optimization_complete:
                    # 显示原始识别结果 + 错误提示
                    self.on_ai_optimization_complete(
                        f"{self.transcription_result}\n\n[提示: AI优化失败 - {error_msg}]"
                    )

        except Exception as e:
            print(f"[TranscriptionHandler] AI优化异常: {e}")
            # 异常也显示在结果区，不占用状态栏
            if self.on_ai_optimization_complete:
                self.on_ai_optimization_complete(
                    f"{self.transcription_result}\n\n[提示: AI优化出错 - {str(e)}]"
                )

    def get_transcription_result(self) -> str:
        """获取转写结果"""
        return self.transcription_result

    def clear_result(self):
        """清空转写结果"""
        self.transcription_result = ""

    def update_status(self, message: str):
        """更新状态（触发回调）"""
        if self.on_status_update:
            self.on_status_update(message)

    def is_busy(self) -> bool:
        """检查是否正在处理"""
        return self.is_processing

    def cancel_processing(self):
        """取消当前处理（标记取消状态）"""
        if self.is_processing:
            self.is_processing = False
            self.update_status("处理已取消")