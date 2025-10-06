#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

提供应用配置的加载、保存、验证和管理功能
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器类"""

    # 默认配置（支持新的分层结构）
    DEFAULT_CONFIG = {
        "ai_services": {
            "default": {
                "api_key": "",
                "base_url": "",
                "model_name": "",
            },
            "correction": {
                "system_prompt": """你是语音识别文本修正专家，请优化以下语音识别文本：

要求：
1. 修正明显的语音识别错误
2. 添加适当的标点符号
3. 保持原意不变
4. 使表达更加流畅自然
5. 如果原文已经很好，可以不做修改

请直接返回优化后的文本，不要添加任何解释：""",
                "system_prompt_file": ""
            },
            "translation": {
                "api_key": "",  # 空则继承default
                "base_url": "", # 空则继承default
                "model_name": "", # 空则继承default
                "target_language": "en",
                "system_prompt": """你是专业翻译助手，请将以下文本翻译成目标语言：

要求：
1. 保持原意不变
2. 语法正确，表达自然
3. 符合目标语言的表达习惯
4. 专业术语翻译准确
5. 保留适当的格式和标点

请直接返回翻译后的文本，不要添加任何解释：""",
                "system_prompt_file": ""
            }
        },
        "language": "zh",
        "use_vad": True,
        "use_punc": True,
        "enable_ai_optimization": True,
        "enable_translation": False,
        "last_audio_device_index": None,  # 上次选择的音频设备索引
        "last_audio_device_name": None,   # 上次选择的音频设备名称（用于验证）
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        if config_file is None:
            # 尝试多个可能的配置文件位置
            possible_paths = [
                os.path.join(os.getcwd(), "doudou_settings.json"),  # 当前目录
                os.path.join(os.getcwd(), "docs", "config", "doudou_settings.json"),  # docs/config
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "doudou_settings.json"),  # 项目根目录
            ]

            # 使用第一个存在的文件，或者默认使用当前目录
            self.config_file = None
            for path in possible_paths:
                if os.path.exists(path):
                    self.config_file = path
                    break

            if self.config_file is None:
                self.config_file = possible_paths[0]  # 默认使用当前目录
        else:
            self.config_file = config_file

        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> bool:
        """
        从文件加载配置

        Returns:
            bool: 加载是否成功
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                # 检查是否需要迁移配置
                if self._needs_migration(loaded_config):
                    print(f"[ConfigManager] 检测到旧版配置，正在迁移...")
                    loaded_config = self._migrate_config(loaded_config)
                    # 自动保存迁移后的配置
                    self.save()

                # 合并加载的配置和默认配置
                self.config = self._deep_merge(self.DEFAULT_CONFIG, loaded_config)
                print(f"[ConfigManager] 配置已从 {self.config_file} 加载")
                return True
            else:
                print(f"[ConfigManager] 配置文件不存在，使用默认配置")
                return False
        except Exception as e:
            print(f"[ConfigManager] 加载配置失败: {e}")
            return False

    def save(self) -> bool:
        """
        保存配置到文件

        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir:  # 只有当目录路径不为空时才创建
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"[ConfigManager] 配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            print(f"[ConfigManager] 保存配置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置项键名
            default: 默认值

        Returns:
            配置项的值，如果不存在则返回默认值
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        设置配置项

        Args:
            key: 配置项键名
            value: 配置项的值
        """
        self.config[key] = value

    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        批量更新配置

        Args:
            config_dict: 配置字典
        """
        self.config.update(config_dict)

    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置

        Returns:
            Dict: 包含所有配置的字典
        """
        return self.config.copy()

    def reset(self) -> None:
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        print("[ConfigManager] 配置已重置为默认值")

    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置完整性

        Returns:
            tuple: (是否有效, 错误信息列表)
        """
        errors = []

        # 验证AI配置
        if self.config.get("enable_ai_optimization", False):
            if not self.config.get("api_key"):
                errors.append("AI优化已启用，但缺少 API Key")
            if not self.config.get("base_url"):
                errors.append("AI优化已启用，但缺少 Base URL")
            if not self.config.get("model_name"):
                errors.append("AI优化已启用，但缺少模型名称")

        # 验证语言设置
        valid_languages = ["zh", "en"]
        if self.config.get("language") not in valid_languages:
            errors.append(f"无效的语言设置: {self.config.get('language')}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典

        Returns:
            Dict: 配置字典
        """
        return self.get_all()

    def from_dict(self, config_dict: Dict[str, Any]) -> None:
        """
        从字典加载配置

        Args:
            config_dict: 配置字典
        """
        self.update(config_dict)

    def get_ai_service_config(self, service_type: str) -> Dict[str, Any]:
        """
        获取AI服务配置，支持继承机制

        Args:
            service_type: 服务类型（'correction', 'translation'等）

        Returns:
            Dict: 合并后的AI服务配置
        """
        ai_services = self.config.get("ai_services", {})
        default_config = ai_services.get("default", {})
        service_config = ai_services.get(service_type, {})

        # 合并配置：service_config覆盖default_config，但只覆盖非空值
        merged = default_config.copy()
        for key, value in service_config.items():
            if value not in [None, "", []]:  # 只覆盖非空值
                merged[key] = value
            elif key in merged:
                # 如果service_config中值为空，但default_config中有值，保持default_config的值
                pass

        return merged

    def set_ai_service_config(self, service_type: str, config: Dict[str, Any]) -> None:
        """
        设置AI服务配置

        Args:
            service_type: 服务类型
            config: 配置字典
        """
        ai_services = self.config.setdefault("ai_services", {})
        ai_services[service_type] = config

    def load_prompt(self, service_type: str) -> str:
        """
        加载Prompt，支持文件和内联两种方式

        Args:
            service_type: 服务类型（'correction', 'translation'等）

        Returns:
            str: Prompt内容
        """
        ai_services = self.config.get("ai_services", {})
        service_config = ai_services.get(service_type, {})

        # 优先使用内联prompt
        if "system_prompt" in service_config and service_config["system_prompt"]:
            return service_config["system_prompt"]

        # 尝试从文件加载
        if "system_prompt_file" in service_config and service_config["system_prompt_file"]:
            prompt_file = Path(service_config["system_prompt_file"])
            if prompt_file.exists():
                try:
                    return prompt_file.read_text(encoding='utf-8')
                except Exception as e:
                    print(f"[ConfigManager] 读取Prompt文件失败: {e}")

        # 返回默认prompt（从DEFAULT_CONFIG中获取）
        default_prompt = self.DEFAULT_CONFIG["ai_services"].get(service_type, {}).get("system_prompt", "")
        return default_prompt

    def save_prompt(self, service_type: str, prompt: str, use_file: bool = False) -> bool:
        """
        保存Prompt

        Args:
            service_type: 服务类型
            prompt: Prompt内容
            use_file: 是否保存到文件

        Returns:
            bool: 是否保存成功
        """
        try:
            ai_services = self.config.setdefault("ai_services", {})
            service_config = ai_services.setdefault(service_type, {})

            if use_file:
                # 确保prompts目录存在
                prompts_dir = Path("prompts")
                prompts_dir.mkdir(exist_ok=True)

                # 保存到文件
                prompt_file = prompts_dir / f"{service_type}.txt"
                prompt_file.write_text(prompt, encoding='utf-8')
                service_config["system_prompt_file"] = str(prompt_file)
                service_config["system_prompt"] = ""  # 清空内联prompt
            else:
                # 保存为内联prompt
                service_config["system_prompt"] = prompt
                service_config["system_prompt_file"] = ""  # 清空文件引用

            return self.save()
        except Exception as e:
            print(f"[ConfigManager] 保存Prompt失败: {e}")
            return False

    def _needs_migration(self, config: Dict[str, Any]) -> bool:
        """
        检查配置是否需要迁移

        Args:
            config: 要检查的配置

        Returns:
            bool: 是否需要迁移
        """
        # 检查是否是旧版配置（没有ai_services结构但有直接的api_key等）
        return ("api_key" in config or "base_url" in config or "model_name" in config) and \
               ("ai_services" not in config)

    def _migrate_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        迁移旧版配置到新的分层结构

        Args:
            old_config: 旧版配置

        Returns:
            Dict: 迁移后的配置
        """
        new_config = self.DEFAULT_CONFIG.copy()

        # 迁移AI相关配置
        if "api_key" in old_config or "base_url" in old_config or "model_name" in old_config:
            ai_services = new_config.setdefault("ai_services", {})
            default_config = ai_services.setdefault("default", {})

            if "api_key" in old_config:
                default_config["api_key"] = old_config.pop("api_key")
            if "base_url" in old_config:
                default_config["base_url"] = old_config.pop("base_url")
            if "model_name" in old_config:
                default_config["model_name"] = old_config.pop("model_name")

        # 迁移其他配置
        for key, value in old_config.items():
            if key not in ["api_key", "base_url", "model_name"]:  # AI配置已处理
                new_config[key] = value

        print(f"[ConfigManager] 配置迁移完成")
        return new_config

    def _deep_merge(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并两个字典，自定义配置覆盖默认配置

        Args:
            default: 默认配置
            custom: 自定义配置

        Returns:
            Dict: 合并后的配置
        """
        result = default.copy()

        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 递归合并嵌套字典
                result[key] = self._deep_merge(result[key], value)
            else:
                # 直接覆盖或添加
                result[key] = value

        return result

    def __repr__(self) -> str:
        """返回配置的字符串表示"""
        return f"ConfigManager(file={self.config_file}, config={self.config})"