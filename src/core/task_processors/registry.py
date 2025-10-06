#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务处理器注册器

管理所有任务处理器的注册、获取和调度
"""

from typing import Dict, Type, Optional, List
from .base_processor import BaseTaskProcessor


class TaskProcessorRegistry:
    """任务处理器注册器"""

    _processors: Dict[str, Type[BaseTaskProcessor]] = {}
    _instances: Dict[str, BaseTaskProcessor] = {}

    @classmethod
    def register(cls, task_type: str, processor_class: Type[BaseTaskProcessor]) -> None:
        """
        注册任务处理器

        Args:
            task_type: 任务类型标识
            processor_class: 处理器类
        """
        cls._processors[task_type] = processor_class
        print(f"[TaskProcessorRegistry] 注册处理器: {task_type} -> {processor_class.__name__}")

    @classmethod
    def get_processor(cls, task_type: str) -> Optional[BaseTaskProcessor]:
        """
        获取任务处理器实例（单例模式）

        Args:
            task_type: 任务类型标识

        Returns:
            BaseTaskProcessor: 处理器实例，如果不存在返回None
        """
        if task_type not in cls._instances:
            if task_type not in cls._processors:
                print(f"[TaskProcessorRegistry] 未找到处理器类型: {task_type}")
                return None

            processor_class = cls._processors[task_type]
            cls._instances[task_type] = processor_class()
            print(f"[TaskProcessorRegistry] 创建处理器实例: {task_type}")

        return cls._instances[task_type]

    @classmethod
    def get_available_processors(cls) -> List[str]:
        """
        获取所有已注册的处理器类型

        Returns:
            List[str]: 任务类型列表
        """
        return list(cls._processors.keys())

    @classmethod
    def unregister(cls, task_type: str) -> bool:
        """
        注销任务处理器

        Args:
            task_type: 任务类型标识

        Returns:
            bool: 是否成功注销
        """
        if task_type in cls._processors:
            del cls._processors[task_type]
            if task_type in cls._instances:
                del cls._instances[task_type]
            print(f"[TaskProcessorRegistry] 注销处理器: {task_type}")
            return True
        return False

    @classmethod
    def clear(cls) -> None:
        """清空所有注册的处理器"""
        cls._processors.clear()
        cls._instances.clear()
        print(f"[TaskProcessorRegistry] 已清空所有处理器")

    @classmethod
    def validate_task_type(cls, task_type: str) -> bool:
        """
        验证任务类型是否已注册

        Args:
            task_type: 任务类型标识

        Returns:
            bool: 是否已注册
        """
        return task_type in cls._processors

    @classmethod
    def get_processor_info(cls) -> Dict[str, str]:
        """
        获取所有处理器的信息

        Returns:
            Dict[str, str]: 任务类型到处理器类名的映射
        """
        return {
            task_type: processor_class.__name__
            for task_type, processor_class in cls._processors.items()
        }


# 装饰器版本的注册器
def register_processor(task_type: str):
    """
    装饰器：自动注册任务处理器

    Args:
        task_type: 任务类型标识

    Returns:
        装饰器函数
    """
    def decorator(processor_class: Type[BaseTaskProcessor]):
        TaskProcessorRegistry.register(task_type, processor_class)
        return processor_class

    return decorator