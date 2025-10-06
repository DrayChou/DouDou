#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块

提供统一的日志记录功能，支持文件和控制台输出
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid


class Logger:
    """统一日志管理器"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Logger._initialized:
            self._setup_logger()
            Logger._initialized = True

    def _setup_logger(self):
        """设置日志器"""
        # 创建logs目录
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)

        # 生成每次启动的唯一标识
        today = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H-%M-%S")
        session_id = str(uuid.uuid4())[:8]  # 取UUID前8位作为会话标识

        # 创建日志文件名（每次启动独立文件）
        self.log_file = self.logs_dir / f"doudou_{today}_{time_str}_{session_id}.log"

        # 配置根日志器
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)

        # 清除现有处理器
        self.root_logger.handlers.clear()

        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器（仅显示WARNING及以上级别）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        self.root_logger.addHandler(console_handler)

        # 文件处理器（记录所有级别）
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.root_logger.addHandler(file_handler)

        # 错误日志文件（仅记录ERROR及以上级别）
        self.error_log_file = self.logs_dir / f"doudou_error_{today}_{time_str}_{session_id}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.root_logger.addHandler(error_handler)

        # 记录日志系统启动
        self.info(f"日志系统已启动 - 会话ID: {session_id}", extra={"context": "system"})

    def debug(self, message: str, **kwargs):
        """调试日志"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """信息日志"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """警告日志"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """错误日志"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self._log(logging.CRITICAL, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """内部日志方法"""
        # 添加上下文信息
        context = kwargs.get('context', '')
        module = kwargs.get('module', '')

        if context:
            formatted_message = f"[{context}] {message}"
        elif module:
            formatted_message = f"[{module}] {message}"
        else:
            formatted_message = message

        self.root_logger.log(level, formatted_message)

    def log_exception(self, message: str, exception: Exception):
        """记录异常信息"""
        self.error(f"{message}: {type(exception).__name__}: {str(exception)}")

        # 记录详细的堆栈跟踪到文件
        import traceback
        self.debug(f"异常堆栈:\n{traceback.format_exc()}", context="exception")

    def get_log_files(self) -> list:
        """获取所有日志文件列表"""
        return sorted(self.logs_dir.glob("*.log"))

    def get_recent_logs(self, lines: int = 50) -> str:
        """获取最近的日志内容"""
        if not self.log_file.exists():
            return "日志文件不存在"

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
        except Exception as e:
            return f"读取日志失败: {str(e)}"

    def get_current_log_files(self) -> dict:
        """获取当前会话的日志文件信息"""
        return {
            "main_log": str(self.log_file),
            "error_log": str(self.error_log_file),
            "session_id": self.log_file.stem.split('_')[-1],  # 从文件名提取会话ID
            "start_time": self.log_file.stem.split('_')[1:4]  # 从文件名提取时间
        }

    def clear_old_logs(self, days: int = 7):
        """清理旧日志文件"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        for log_file in self.get_log_files():
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    self.info(f"已删除旧日志文件: {log_file}")
            except Exception as e:
                self.warning(f"删除日志文件失败 {log_file}: {str(e)}")


# 创建全局日志器实例
logger = Logger()

# 提供便捷的函数接口
def debug(message: str, **kwargs):
    logger.debug(message, **kwargs)

def info(message: str, **kwargs):
    logger.info(message, **kwargs)

def warning(message: str, **kwargs):
    logger.warning(message, **kwargs)

def error(message: str, **kwargs):
    logger.error(message, **kwargs)

def critical(message: str, **kwargs):
    logger.critical(message, **kwargs)

def log_exception(message: str, exception: Exception):
    logger.log_exception(message, exception)

def get_logger():
    """获取日志器实例"""
    return logger


# 日志系统不再替换全局print函数，避免潜在的递归问题
# 如果需要同时输出到日志和控制台，请直接使用logger方法