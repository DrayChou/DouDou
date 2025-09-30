#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音识别流水线模块

提供语音识别流水线功能，支持直接FunASR集成和服务器调用
"""

import os
import sys
import json
import subprocess
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .direct_funasr import DirectFunASR

logger = logging.getLogger(__name__)


class RecognitionPipeline:
    """语音识别流水线类"""

    def __init__(self, use_direct_integration: bool = True, funasr_server_path: Optional[str] = None):
        """
        初始化识别流水线

        Args:
            use_direct_integration: 是否使用直接集成模式
            funasr_server_path: FunASR服务器脚本路径，如果为None则使用默认路径
        """
        self.use_direct_integration = use_direct_integration

        if use_direct_integration:
            self.direct_funasr = DirectFunASR()
        else:
            if funasr_server_path is None:
                # 使用 src 目录下的 funasr_server.py
                self.funasr_server_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "funasr_server.py"
                )
            else:
                self.funasr_server_path = funasr_server_path

    def transcribe_audio(self, audio_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            options: 识别选项，可选参数：
                - use_vad: bool, 是否使用VAD
                - use_punc: bool, 是否使用标点恢复
                - language: str, 语言代码

        Returns:
            Dict: 识别结果，包含以下字段：
                - success: bool, 是否成功
                - text: str, 识别文本
                - confidence: float, 置信度
                - duration: float, 音频时长
                - error: str, 错误信息（如果失败）
        """
        if self.use_direct_integration:
            # 使用直接集成模式
            return self.direct_funasr.transcribe_audio(audio_path, options)
        else:
            # 使用服务器模式（后备方案）
            return self._transcribe_via_server(audio_path, options)

    def _transcribe_via_server(self, audio_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通过服务器模式转录音频"""
        try:
            # 检查FunASR服务器脚本
            if not os.path.exists(self.funasr_server_path):
                return {
                    "success": False,
                    "error": "FunASR服务器脚本不存在",
                    "text": "FunASR服务器脚本不存在"
                }

            # 检查音频文件
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "error": f"音频文件不存在: {audio_path}",
                    "text": f"音频文件不存在: {audio_path}"
                }

            # 准备命令输入
            input_data = {
                "action": "transcribe",
                "audio_path": audio_path,
                "options": options or {
                    "use_vad": True,
                    "use_punc": True,
                    "language": "zh"
                }
            }

            input_text = json.dumps(input_data, ensure_ascii=False) + '\n'
            print(f"[RecognitionPipeline] 开始通过服务器转录音频: {audio_path}")

            # 运行FunASR服务器进行转录
            process = subprocess.Popen(
                [sys.executable, self.funasr_server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
            )

            try:
                stdout, stderr = process.communicate(input=input_text, timeout=120)

                if process.returncode == 0:
                    lines = stdout.strip().split('\n')
                    if len(lines) >= 2:
                        try:
                            result_line = lines[-1]
                            output = json.loads(result_line)

                            if output.get("success"):
                                print(f"[RecognitionPipeline] 服务器转录成功")
                                return {
                                    "success": True,
                                    "text": output.get("text", ""),
                                    "confidence": output.get("confidence", 0.0),
                                    "duration": output.get("duration", 0.0)
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": output.get("error", "转录失败"),
                                    "text": f"转录失败: {output.get('error', '未知错误')}"
                                }
                        except json.JSONDecodeError as je:
                            return {
                                "success": False,
                                "error": f"解析转录结果失败: {str(je)}",
                                "text": f"解析失败，原始输出: {stdout[:200]}..."
                            }
                    else:
                        return {
                            "success": False,
                            "error": "服务器响应格式错误",
                            "text": f"响应行数不足: {len(lines)}, 内容: {stdout[:200]}..."
                        }
                else:
                    return {
                        "success": False,
                        "error": f"服务器执行失败 (代码: {process.returncode})",
                        "text": f"错误信息: {stderr[:200]}..."
                    }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": "转录超时",
                    "text": "转录超时，请稍后重试"
                }
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": f"转录异常: {str(e)}"
            }

    def check_funasr_status(self) -> Dict[str, Any]:
        """检查FunASR状态"""
        if self.use_direct_integration:
            return self.direct_funasr.check_status()
        else:
            return self._check_server_status()

    def _check_server_status(self) -> Dict[str, Any]:
        """检查服务器状态"""
        try:
            if not os.path.exists(self.funasr_server_path):
                return {
                    "success": False,
                    "installed": False,
                    "error": "FunASR服务器脚本不存在"
                }

            # 尝试运行状态检查命令
            input_data = {"action": "status"}
            input_text = json.dumps(input_data, ensure_ascii=False) + '\n'

            process = subprocess.Popen(
                [sys.executable, self.funasr_server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )

            try:
                stdout, stderr = process.communicate(input=input_text, timeout=30)
                lines = stdout.strip().split('\n')
                if len(lines) >= 2:
                    status_line = lines[-1]
                    status = json.loads(status_line)
                    return status
                else:
                    return {
                        "success": False,
                        "error": "无法获取FunASR状态"
                    }
            finally:
                if process.poll() is None:
                    process.terminate()

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }