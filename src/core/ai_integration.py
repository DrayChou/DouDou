#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 集成模块

提供AI文本优化和翻译功能
"""

import json
from typing import Dict, Any, Optional


class AIProcessor:
    """AI处理器类"""

    def __init__(self, api_key: str, base_url: str, model_name: str):
        """
        初始化AI处理器

        Args:
            api_key: API密钥
            base_url: API基础URL
            model_name: 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    def optimize_text(self, text: str, context_history: Optional[list] = None) -> Dict[str, Any]:
        """
        使用AI优化文本

        Args:
            text: 需要优化的原始文本
            context_history: 上下文历史（最近3条识别结果）

        Returns:
            Dict: 优化结果，包含以下字段：
                - success: bool, 是否成功
                - text: str, 优化后的文本
                - error: str, 错误信息（如果失败）
        """
        try:
            # 检查配置
            if not all([self.api_key, self.base_url, self.model_name]):
                return {
                    "success": False,
                    "error": "AI配置不完整，请在设置中配置API Key、Base URL和模型名称"
                }

            # 构建上下文部分
            context_section = ""
            if context_history and len(context_history) > 0:
                context_section = "\n\n上下文参考（之前的识别结果）：\n"
                for i, ctx in enumerate(context_history, 1):
                    context_section += f"{i}. {ctx}\n"

            # 构建优化提示词
            optimization_prompt = f"""请优化以下语音识别文本，修正可能的识别错误，补充标点符号，使其更符合中文表达习惯：
{context_section}
当前需要优化的文本：{text}

优化要求：
1. 参考上下文理解当前文本的语境
2. 修正明显的语音识别错误
3. 添加适当的标点符号
4. 保持原意不变
5. 使表达更加流畅自然
6. 如果原文已经很好，可以不做修改

请直接返回优化后的文本，不要添加任何解释："""

            # 调用AI API
            optimized_text = self._call_api(optimization_prompt)

            if optimized_text:
                return {
                    "success": True,
                    "text": optimized_text.strip()
                }
            else:
                return {
                    "success": False,
                    "error": "AI返回空结果"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _call_api(self, prompt: str) -> Optional[str]:
        """
        调用AI API

        Args:
            prompt: 提示词

        Returns:
            Optional[str]: API返回的文本，失败返回None
        """
        try:
            import requests

            # 构建API请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }

            # 确保base_url格式正确
            api_url = self.base_url
            if not api_url.endswith('/'):
                api_url += '/'
            if not api_url.endswith('chat/completions'):
                api_url += 'chat/completions'

            print(f"[AIProcessor] 调用AI API: {api_url}")

            # 发送请求
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    optimized_text = result['choices'][0]['message']['content'].strip()
                    print(f"[AIProcessor] AI优化成功")
                    return optimized_text
                else:
                    print(f"[AIProcessor] AI API响应格式错误: {result}")
                    return None
            else:
                print(f"[AIProcessor] AI API请求失败: {response.status_code}, {response.text}")
                return None

        except Exception as e:
            print(f"[AIProcessor] AI API调用异常: {e}")
            return None

    def translate_text(self, text: str, target_language: str = "en") -> Dict[str, Any]:
        """
        翻译文本（预留功能）

        Args:
            text: 需要翻译的文本
            target_language: 目标语言代码

        Returns:
            Dict: 翻译结果
        """
        # TODO: 实现翻译功能
        return {
            "success": False,
            "error": "翻译功能尚未实现"
        }