#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心功能模块导出。"""

from .audio_engine import (
    AUDIO_BACKEND_NAME,
    AudioDeviceInfo,
    AudioEngine,
    AudioStreamConfig,
    AudioTestResult,
)
from .ai_integration import AIProcessor
from .recognition_pipeline import RecognitionPipeline
from .vad_system import HybridVAD, HybridVADSegmenter, VADConfig, VADSegment, create_chinese_optimized_config
from .audio_recorder import AudioRecorder
from .transcription_handler import TranscriptionHandler
from .task_manager import (
    TaskManager, TaskStatus, TaskPriority, AudioSegment,
    RecognitionTask, AIOptimizationTask, TaskStatistics
)
from .continuous_recorder import ContinuousAudioRecorder, RecorderConfig

__all__ = [
    "AUDIO_BACKEND_NAME",
    "AudioDeviceInfo",
    "AudioEngine",
    "AudioStreamConfig",
    "AudioTestResult",
    "AIProcessor",
    "RecognitionPipeline",
    "HybridVAD",
    "HybridVADSegmenter",
    "VADConfig",
    "VADSegment",
    "create_chinese_optimized_config",
    "AudioRecorder",
    "TranscriptionHandler",
    "TaskManager",
    "TaskStatus",
    "TaskPriority",
    "AudioSegment",
    "RecognitionTask",
    "AIOptimizationTask",
    "TaskStatistics",
    "ContinuousAudioRecorder",
    "RecorderConfig",
]
