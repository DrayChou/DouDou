#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接FunASR集成模块

将FunASR直接集成到应用程序中，避免进程间通信开销
"""

import os
import logging
import traceback
from typing import Dict, Any, Optional
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class DirectFunASR:
    """直接FunASR集成类"""

    def __init__(self):
        """初始化FunASR模型"""
        self.asr_model = None
        self.vad_model = None
        self.punc_model = None
        self.initialized = False
        self.transcription_count = 0
        self.device = self._detect_device()
        logger.info(f"设备检测完成: {self.device}")

    def _detect_device(self) -> str:
        """
        自动检测最佳可用设备

        优先级: CUDA GPU > MPS (Apple Silicon) > XPU (Intel GPU) > CPU

        Returns:
            str: 设备名称 ("cuda:0", "mps", "xpu", "cpu")
        """
        try:
            import torch

            # 1. 检测NVIDIA CUDA GPU
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                logger.info(f"检测到CUDA GPU: {gpu_name}, 显存: {gpu_memory:.2f}GB")
                return "cuda:0"

            # 2. 检测Apple Silicon MPS
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                logger.info("检测到Apple Silicon MPS加速")
                return "mps"

            # 3. 检测Intel XPU
            if hasattr(torch, 'xpu') and torch.xpu.is_available():
                logger.info("检测到Intel XPU加速")
                return "xpu"

            # 4. 降级到CPU
            logger.info("未检测到GPU，使用CPU模式")
            return "cpu"

        except ImportError:
            logger.warning("PyTorch未安装，无法检测设备，默认使用CPU")
            return "cpu"
        except Exception as e:
            logger.warning(f"设备检测失败: {e}，默认使用CPU")
            return "cpu"

    def initialize(self) -> Dict[str, Any]:
        """初始化FunASR模型"""
        if self.initialized:
            return {"success": True, "message": "模型已初始化"}

        try:
            logger.info("开始加载FunASR模型...")
            start_time = time.time()

            # 导入FunASR
            from funasr import AutoModel

            # 加载ASR模型（使用自动检测的设备）
            logger.info(f"加载ASR模型到 {self.device}...")
            self.asr_model = AutoModel(
                model="damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                model_revision="v2.0.4",
                disable_update=True,
                device=self.device,
            )

            # 加载VAD模型（使用自动检测的设备）
            logger.info(f"加载VAD模型到 {self.device}...")
            self.vad_model = AutoModel(
                model="damo/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                model_revision="v2.0.4",
                disable_update=True,
                device=self.device,
            )

            # 加载标点模型（使用自动检测的设备）
            logger.info(f"加载标点恢复模型到 {self.device}...")
            self.punc_model = AutoModel(
                model="damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
                model_revision="v2.0.4",
                disable_update=True,
                device=self.device,
            )

            total_time = time.time() - start_time
            self.initialized = True
            logger.info(f"FunASR模型初始化完成，耗时: {total_time:.2f}秒，设备: {self.device}")

            return {
                "success": True,
                "message": f"FunASR模型初始化成功，耗时: {total_time:.2f}秒，设备: {self.device}",
                "device": self.device
            }

        except ImportError as e:
            error_msg = "FunASR未安装，请先安装FunASR: pip install funasr"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "import_error"}
        except Exception as e:
            error_msg = f"FunASR模型初始化失败: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"success": False, "error": error_msg, "type": "init_error"}

    def transcribe_audio(self, audio_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        直接转录音频文件

        Args:
            audio_path: 音频文件路径
            options: 识别选项

        Returns:
            Dict: 识别结果
        """
        if not self.initialized:
            init_result = self.initialize()
            if not init_result["success"]:
                return init_result

        try:
            # 检查音频文件
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "error": f"音频文件不存在: {audio_path}",
                    "text": f"音频文件不存在: {audio_path}"
                }

            logger.info(f"开始转录音频: {audio_path}")

            # 设置默认选项
            default_options = {
                "use_vad": True,
                "use_punc": True,
                "language": "zh",
                "batch_size_s": 60,
            }

            if options:
                default_options.update(options)

            # VAD处理（如果启用）
            if default_options["use_vad"] and self.vad_model:
                try:
                    vad_result = self.vad_model.generate(
                        input=audio_path,
                        batch_size_s=default_options["batch_size_s"]
                    )
                    logger.info("VAD处理完成")
                except Exception as e:
                    logger.warning(f"VAD处理失败: {str(e)}")

            # ASR识别
            asr_result = self.asr_model.generate(
                input=audio_path,
                batch_size_s=default_options["batch_size_s"],
                cache={},
            )

            # 提取识别文本
            if isinstance(asr_result, list) and len(asr_result) > 0:
                if isinstance(asr_result[0], dict) and "text" in asr_result[0]:
                    raw_text = asr_result[0]["text"]
                else:
                    raw_text = str(asr_result[0])
            else:
                raw_text = str(asr_result)

            logger.info(f"ASR识别完成，原始文本: {raw_text[:100]}...")

            # 标点恢复（如果启用）
            final_text = raw_text
            if default_options["use_punc"] and self.punc_model and raw_text.strip():
                try:
                    punc_result = self.punc_model.generate(input=raw_text)
                    if isinstance(punc_result, list) and len(punc_result) > 0:
                        if isinstance(punc_result[0], dict) and "text" in punc_result[0]:
                            final_text = punc_result[0]["text"]
                        else:
                            final_text = str(punc_result[0])
                    logger.info("标点恢复完成")
                except Exception as e:
                    logger.warning(f"标点恢复失败: {str(e)}")

            # 获取音频时长
            duration = self._get_audio_duration(audio_path)
            self.transcription_count += 1

            # 计算置信度
            confidence = 0.0
            if isinstance(asr_result, list) and len(asr_result) > 0:
                if isinstance(asr_result[0], dict):
                    confidence = getattr(asr_result[0], "confidence", 0.0)

            result = {
                "success": True,
                "text": final_text,
                "raw_text": raw_text,
                "confidence": confidence,
                "duration": duration,
                "language": "zh-CN",
            }

            logger.info(f"转录完成，最终文本: {final_text[:100]}...")
            return result

        except Exception as e:
            error_msg = f"音频转录失败: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"success": False, "error": error_msg, "text": error_msg}

    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        try:
            import librosa
            duration = librosa.get_duration(filename=audio_path)
            return duration
        except:
            return 0.0

    def check_status(self) -> Dict[str, Any]:
        """检查FunASR状态"""
        try:
            import funasr

            return {
                "success": True,
                "installed": True,
                "initialized": self.initialized,
                "device": self.device,
                "version": getattr(funasr, "__version__", "unknown"),
                "models": {
                    "asr": self.asr_model is not None,
                    "vad": self.vad_model is not None,
                    "punc": self.punc_model is not None,
                },
            }
        except ImportError:
            return {
                "success": False,
                "installed": False,
                "initialized": False,
                "device": "unknown",
                "error": "FunASR未安装",
            }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "transcription_count": self.transcription_count,
            "initialized": self.initialized,
            "models_loaded": {
                "asr": self.asr_model is not None,
                "vad": self.vad_model is not None,
                "punc": self.punc_model is not None,
            },
        }