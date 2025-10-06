#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI文本修正处理器

处理语音识别结果的AI优化和修正
"""

from typing import Dict, Any, Optional
from .base_processor import BaseTaskProcessor
from .registry import register_processor


@register_processor("correction")
class CorrectionProcessor(BaseTaskProcessor):
    """AI文本修正处理器"""

    task_type = "correction"

    def __init__(self):
        """初始化修正处理器"""
        super().__init__()
        # 默认的修正prompt（如果配置中没有）
        self.default_prompt = """你是语音识别文本修正专家，请优化以下语音识别文本：

要求：
1. 修正明显的语音识别错误
2. 添加适当的标点符号
3. 保持原意不变
4. 使表达更加流畅自然
5. 如果原文已经很好，可以不做修改

请直接返回优化后的文本，不要添加任何解释："""

    def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理AI文本修正任务

        Args:
            task_data: 任务数据，包含:
                - task: AIOptimizationTask实例
                - base_config: 完整的应用配置

        Returns:
            Dict: 处理结果
        """
        try:
            task = task_data.get("task")
            base_config = task_data.get("base_config", {})

            if not task:
                return {"success": False, "error": "缺少任务数据"}

            # 获取原文
            original_text = getattr(task, 'original_text', '')
            if not original_text or not original_text.strip():
                return {"success": False, "error": "原文为空"}

            # 验证配置
            if not self.validate_config(base_config):
                return {"success": False, "error": self.last_error}

            # 获取AI配置和Prompt
            ai_config = self.get_ai_config(base_config)
            prompt = self.get_prompt(base_config) or self.default_prompt

            # 获取上下文历史（如果可用）
            context_history = self._get_context_history(task_data)

            # 构建完整的提示词
            full_prompt = self._build_correction_prompt(original_text, prompt, context_history)

            # 调用AI API
            optimized_text = self.call_ai_api(full_prompt, ai_config)

            if optimized_text:
                # 更新任务结果
                if hasattr(task, 'optimized_text'):
                    task.optimized_text = optimized_text.strip()

                return {
                    "success": True,
                    "result": optimized_text.strip(),
                    "original_text": original_text,
                    "context_used": bool(context_history)
                }
            else:
                return {
                    "success": False,
                    "error": self.last_error or "AI返回空结果",
                    "original_text": original_text
                }

        except Exception as e:
            self.last_error = f"处理修正任务时发生异常: {str(e)}"
            return {"success": False, "error": self.last_error}

    def _get_context_history(self, task_data: Dict[str, Any]) -> Optional[list]:
        """
        获取上下文历史

        Args:
            task_data: 任务数据

        Returns:
            Optional[list]: 上下文历史，如果没有则返回None
        """
        # 尝试从多个来源获取上下文
        if 'context_history' in task_data:
            return task_data['context_history']

        # 如果有callback方法，尝试获取
        if hasattr(task_data, 'get_context_history') and callable(task_data.get_context_history):
            try:
                return task_data.get_context_history()
            except Exception as e:
                print(f"[CorrectionProcessor] 获取上下文历史失败: {e}")

        return None

    def _build_correction_prompt(self, text: str, base_prompt: str, context_history: Optional[list] = None) -> str:
        """
        构建完整的修正提示词

        Args:
            text: 需要修正的文本
            base_prompt: 基础提示词
            context_history: 上下文历史

        Returns:
            str: 完整的提示词
        """
        # 构建上下文部分
        context_section = ""
        if context_history and len(context_history) > 0:
            context_section = "\n\n上下文参考（之前的识别结果）：\n"
            for i, ctx in enumerate(context_history, 1):
                context_section += f"{i}. {ctx}\n"

        # 组合完整提示词
        full_prompt = f"""{base_prompt}

{context_section}

当前需要优化的文本：{text}"""

        return full_prompt

    def get_default_prompt(self) -> str:
        """
        获取默认的修正Prompt

        Returns:
            str: 默认Prompt
        """
        return self.default_prompt

    def validate_correction_input(self, text: str) -> bool:
        """
        验证修正输入是否有效

        Args:
            text: 输入文本

        Returns:
            bool: 是否有效
        """
        if not text or not text.strip():
            self.last_error = "输入文本为空"
            return False

        # 可以添加更多验证逻辑
        # 比如文本长度限制、字符集检查等

        return True