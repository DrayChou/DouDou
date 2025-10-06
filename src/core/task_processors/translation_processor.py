#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译处理器

处理文本翻译任务，支持多语言翻译
"""

from typing import Dict, Any, Optional
from .base_processor import BaseTaskProcessor
from .registry import register_processor


@register_processor("translation")
class TranslationProcessor(BaseTaskProcessor):
    """翻译处理器"""

    task_type = "translation"

    def __init__(self):
        """初始化翻译处理器"""
        super().__init__()
        # 默认的翻译prompt（如果配置中没有）
        self.default_prompt = """你是专业翻译助手，请将以下文本翻译成目标语言：

要求：
1. 保持原意不变
2. 语法正确，表达自然
3. 符合目标语言的表达习惯
4. 专业术语翻译准确
5. 保留适当的格式和标点

请直接返回翻译后的文本，不要添加任何解释："""

        # 支持的语言映射
        self.language_map = {
            "zh": "中文",
            "en": "英文",
            "ja": "日文",
            "ko": "韩文",
            "fr": "法文",
            "de": "德文",
            "es": "西班牙文",
            "ru": "俄文",
            "it": "意大利文",
            "pt": "葡萄牙文"
        }

    def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理翻译任务

        Args:
            task_data: 任务数据，包含:
                - task: TranslationTask实例
                - base_config: 完整的应用配置

        Returns:
            Dict: 处理结果
        """
        try:
            task = task_data.get("task")
            base_config = task_data.get("base_config", {})

            if not task:
                return {"success": False, "error": "缺少任务数据"}

            # 获取翻译参数
            original_text = getattr(task, 'original_text', '')
            source_language = getattr(task, 'source_language', 'zh')
            target_language = getattr(task, 'target_language', 'en')

            if not original_text or not original_text.strip():
                return {"success": False, "error": "原文为空"}

            # 验证配置
            if not self.validate_config(base_config):
                return {"success": False, "error": self.last_error}

            # 验证语言设置
            if not self._validate_languages(source_language, target_language):
                return {"success": False, "error": self.last_error}

            # 获取AI配置和Prompt
            ai_config = self.get_ai_config(base_config)
            prompt = self.get_prompt(base_config) or self.default_prompt

            # 从配置中获取目标语言（如果任务中没有指定）
            if not target_language or target_language == 'auto':
                target_language = ai_config.get('target_language', 'en')

            # 构建完整的提示词
            full_prompt = self._build_translation_prompt(
                original_text, prompt, source_language, target_language
            )

            # 调用AI API
            translated_text = self.call_ai_api(full_prompt, ai_config)

            if translated_text:
                # 更新任务结果
                if hasattr(task, 'translated_text'):
                    task.translated_text = translated_text.strip()

                return {
                    "success": True,
                    "result": translated_text.strip(),
                    "original_text": original_text,
                    "source_language": source_language,
                    "target_language": target_language,
                    "target_language_name": self.language_map.get(target_language, target_language)
                }
            else:
                return {
                    "success": False,
                    "error": self.last_error or "翻译服务返回空结果",
                    "original_text": original_text,
                    "source_language": source_language,
                    "target_language": target_language
                }

        except Exception as e:
            self.last_error = f"处理翻译任务时发生异常: {str(e)}"
            return {"success": False, "error": self.last_error}

    def _validate_languages(self, source_language: str, target_language: str) -> bool:
        """
        验证语言设置

        Args:
            source_language: 源语言
            target_language: 目标语言

        Returns:
            bool: 是否有效
        """
        if not source_language or not target_language:
            self.last_error = "源语言或目标语言为空"
            return False

        if source_language == target_language:
            self.last_error = "源语言和目标语言不能相同"
            return False

        # 检查语言是否在支持列表中
        if source_language not in self.language_map:
            self.last_error = f"不支持的源语言: {source_language}"
            return False

        if target_language not in self.language_map:
            self.last_error = f"不支持的目标语言: {target_language}"
            return False

        return True

    def _build_translation_prompt(self, text: str, base_prompt: str, source_language: str, target_language: str) -> str:
        """
        构建完整的翻译提示词

        Args:
            text: 需要翻译的文本
            base_prompt: 基础提示词
            source_language: 源语言
            target_language: 目标语言

        Returns:
            str: 完整的提示词
        """
        source_name = self.language_map.get(source_language, source_language)
        target_name = self.language_map.get(target_language, target_language)

        full_prompt = f"""{base_prompt}

源语言：{source_name} ({source_language})
目标语言：{target_name} ({target_language})

需要翻译的文本：{text}"""

        return full_prompt

    def get_default_prompt(self) -> str:
        """
        获取默认的翻译Prompt

        Returns:
            str: 默认Prompt
        """
        return self.default_prompt

    def get_supported_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表

        Returns:
            Dict[str, str]: 语言代码到语言名称的映射
        """
        return self.language_map.copy()

    def validate_translation_input(self, text: str, source_language: str, target_language: str) -> bool:
        """
        验证翻译输入是否有效

        Args:
            text: 输入文本
            source_language: 源语言
            target_language: 目标语言

        Returns:
            bool: 是否有效
        """
        if not text or not text.strip():
            self.last_error = "输入文本为空"
            return False

        return self._validate_languages(source_language, target_language)

    def detect_language(self, text: str) -> Optional[str]:
        """
        检测文本语言（简单实现，可扩展）

        Args:
            text: 输入文本

        Returns:
            Optional[str]: 检测到的语言代码，如果无法检测返回None
        """
        # 简单的语言检测逻辑
        # 可以集成更复杂的语言检测库

        # 检测是否包含中文字符
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        if chinese_chars > len(text) * 0.3:  # 如果中文字符占比超过30%
            return "zh"

        # 检测是否包含日文字符
        japanese_chars = sum(1 for char in text if
                           '\u3040' <= char <= '\u309f' or  # 平假名
                           '\u30a0' <= char <= '\u30ff' or  # 片假名
                           '\u4e00' <= char <= '\u9fff')    # 汉字
        if japanese_chars > len(text) * 0.3:
            return "ja"

        # 检测韩文字符
        korean_chars = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
        if korean_chars > len(text) * 0.3:
            return "ko"

        # 默认认为是英文
        return "en"