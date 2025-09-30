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

    # 默认配置
    DEFAULT_CONFIG = {
        "api_key": "",
        "base_url": "",
        "model_name": "",
        "language": "zh",
        "use_vad": True,
        "use_punc": True,
        "enable_ai_optimization": True,
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        if config_file is None:
            # 使用当前工作目录的配置文件
            self.config_file = os.path.join(os.getcwd(), "doudou_settings.json")
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
                    # 合并加载的配置和默认配置
                    self.config.update(loaded_config)
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
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

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

    def __repr__(self) -> str:
        """返回配置的字符串表示"""
        return f"ConfigManager(file={self.config_file}, config={self.config})"