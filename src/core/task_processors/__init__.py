#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务处理器模块

提供可插拔的任务处理器架构，支持AI修正、翻译等多种任务类型
"""

from .base_processor import BaseTaskProcessor
from .correction_processor import CorrectionProcessor
from .translation_processor import TranslationProcessor
from .registry import TaskProcessorRegistry

__all__ = [
    'BaseTaskProcessor',
    'CorrectionProcessor',
    'TranslationProcessor',
    'TaskProcessorRegistry'
]