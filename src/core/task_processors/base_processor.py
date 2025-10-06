#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务处理器基类

定义所有任务处理器的通用接口和行为
"""

import abc
from typing import Dict, Any, Optional
import requests
from utils.logger import get_logger

# Use unified logger
logger = get_logger()


class BaseTaskProcessor(abc.ABC):
    """任务处理器抽象基类"""

    task_type: str = ""  # 子类必须定义任务类型

    def __init__(self):
        """初始化任务处理器"""
        self.last_error: Optional[str] = None

    @abc.abstractmethod
    def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务的核心逻辑

        Args:
            task_data: 任务数据，包含:
                - task: 任务对象
                - base_config: 完整的应用配置

        Returns:
            Dict: 处理结果，包含:
                - success: bool, 是否成功
                - result: Any, 处理结果
                - error: str, 错误信息（如果失败）
        """
        pass

    def get_ai_config(self, base_config: Dict) -> Dict[str, Any]:
        """
        获取合并后的AI配置，支持继承机制

        Args:
            base_config: 完整的应用配置

        Returns:
            Dict: 合并后的AI配置
        """
        ai_services = base_config.get("ai_services", {})
        default_config = ai_services.get("default", {})
        service_config = ai_services.get(self.task_type, {})

        # 合并配置：service_config覆盖default_config，但只覆盖非空值
        merged = default_config.copy()
        for key, value in service_config.items():
            if value not in [None, "", []]:  # 只覆盖非空值
                merged[key] = value
            elif key in merged:
                # 如果service_config中值为空，但default_config中有值，保持default_config的值
                pass

        return merged

    def get_prompt(self, base_config: Dict) -> str:
        """
        获取Prompt，支持文件和内联两种方式

        Args:
            base_config: 完整的应用配置

        Returns:
            str: Prompt内容
        """
        ai_services = base_config.get("ai_services", {})
        service_config = ai_services.get(self.task_type, {})

        # 优先使用内联prompt
        if "system_prompt" in service_config and service_config["system_prompt"]:
            return service_config["system_prompt"]

        # 尝试从文件加载（如果配置中有文件路径）
        if "system_prompt_file" in service_config and service_config["system_prompt_file"]:
            try:
                from pathlib import Path
                prompt_file = Path(service_config["system_prompt_file"])
                if prompt_file.exists():
                    return prompt_file.read_text(encoding='utf-8')
            except Exception as e:
                print(f"[{self.task_type}Processor] 读取Prompt文件失败: {e}")

        # 返回空字符串，子类应该提供默认prompt
        return ""

    def call_ai_api(self, prompt: str, ai_config: Dict[str, Any]) -> Optional[str]:
        """
        调用AI API的通用方法

        Args:
            prompt: 完整的提示词
            ai_config: AI配置

        Returns:
            Optional[str]: AI返回的文本，失败返回None
        """
        try:
            # 检查配置完整性
            if not all([ai_config.get("api_key"), ai_config.get("base_url"), ai_config.get("model_name")]):
                self.last_error = f"AI配置不完整，请检查API Key、Base URL和模型名称"
                return None

            # 构建API请求
            headers = {
                "Authorization": f"Bearer {ai_config['api_key']}",
                "Content-Type": "application/json"
            }

            data = {
                "model": ai_config["model_name"],
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 4096
            }

            # 确保base_url格式正确
            api_url = ai_config["base_url"]
            if not api_url.endswith('/'):
                api_url += '/'
            if not api_url.endswith('chat/completions'):
                api_url += 'chat/completions'

            print(f"[{self.task_type}Processor] 调用AI API: {api_url}")
            print(f"[{self.task_type}Processor] 模型: {ai_config['model_name']}, prompt长度: {len(prompt)}")

            # 发送请求
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    response_text = result['choices'][0]['message']['content'].strip()
                    finish_reason = result['choices'][0].get('finish_reason', 'unknown')
                    print(f"[{self.task_type}Processor] AI调用成功, finish_reason={finish_reason}, 返回长度={len(response_text)}")
                    return response_text
                else:
                    self.last_error = f"AI响应格式错误: {result}"
                    return None
            else:
                error_detail = response.text[:200] if response.text else "无详细信息"
                self.last_error = f"AI API调用失败: HTTP {response.status_code}, {error_detail}"
                logger.error(f"[{self.task_type}Processor] {self.last_error}")
                print(f"[ERROR] {self.last_error}")
                if response.status_code == 502:
                    print(f"[HINT] HTTP 502通常表示AI服务未启动或崩溃，请检查: {ai_config.get('base_url')}")
                return None

        except requests.exceptions.Timeout:
            self.last_error = f"AI API调用超时"
            return None
        except requests.exceptions.ConnectionError as e:
            self.last_error = f"AI API连接失败，请检查服务是否启动: {ai_config.get('base_url')}"
            logger.error(f"[{self.task_type}Processor] {self.last_error}")
            print(f"[ERROR] {self.last_error}")
            return None
        except Exception as e:
            self.last_error = f"AI API调用异常: {str(e)}"
            return None

    def validate_config(self, base_config: Dict) -> bool:
        """
        验证配置是否有效

        Args:
            base_config: 完整的应用配置

        Returns:
            bool: 配置是否有效
        """
        ai_config = self.get_ai_config(base_config)

        required_keys = ["api_key", "base_url", "model_name"]
        for key in required_keys:
            if not ai_config.get(key):
                self.last_error = f"AI配置缺少必要项: {key}"
                return False

        return True

    def get_last_error(self) -> Optional[str]:
        """获取最后一次错误信息"""
        return self.last_error

    def __str__(self) -> str:
        """返回处理器描述"""
        return f"{self.__class__.__name__}(task_type='{self.task_type}')"
