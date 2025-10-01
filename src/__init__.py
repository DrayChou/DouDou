#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DouDou - 智能语音助手主包。"""

__version__ = "1.0.0"
__author__ = "QuQu Team"

from .core import (  # re-export core primitives for convenience
    AUDIO_BACKEND_NAME,
    AudioDeviceInfo,
    AudioEngine,
    AudioStreamConfig,
    AudioTestResult,
    AIProcessor,
    HybridVAD,
    HybridVADSegmenter,
    RecognitionPipeline,
    VADConfig,
    VADSegment,
)

__all__ = [
    "__version__",
    "__author__",
    "AUDIO_BACKEND_NAME",
    "AudioDeviceInfo",
    "AudioEngine",
    "AudioStreamConfig",
    "AudioTestResult",
    "AIProcessor",
    "HybridVAD",
    "HybridVADSegmenter",
    "RecognitionPipeline",
    "VADConfig",
    "VADSegment",
]
