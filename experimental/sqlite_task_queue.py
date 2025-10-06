#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于SQLite的简单任务队列实现示例

这是一个针对QuQu项目的轻量级任务队列解决方案，
支持持久化、跨平台、零第三方依赖
"""

import sqlite3
import json
import time
import threading
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from queue import Queue, Empty
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(Enum):
    RECOGNITION = "recognition"
    CORRECTION = "correction"
    TRANSLATION = "translation"

@dataclass
class SQLiteTask:
    task_id: str
    task_type: str
    data: Dict[str, Any]
    status: str = TaskStatus.PENDING.value
    priority: int = 0
    created_at: float = None
    updated_at: float = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        self.updated_at = self.created_at

class SQLiteTaskQueue:
    """基于SQLite的轻量级任务队列"""

    def __init__(self, db_path: str = "ququ_tasks.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    created_at REAL,
                    updated_at REAL,
                    result TEXT,
                    error TEXT
                )
            ''')

            # 创建索引提高查询性能
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_status_priority
                ON tasks(status, priority DESC, created_at)
            ''')
            conn.commit()

    def put(self, task: SQLiteTask) -> bool:
        """添加任务到队列"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO tasks
                        (task_id, task_type, data, status, priority, created_at, updated_at, result, error)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        task.task_id,
                        task.task_type,
                        json.dumps(task.data),
                        task.status,
                        task.priority,
                        task.created_at,
                        task.updated_at,
                        json.dumps(task.result) if task.result else None,
                        task.error
                    ))
                    conn.commit()
                return True
            except Exception as e:
                print(f"保存任务失败: {e}")
                return False

    def get(self, task_type: Optional[str] = None, timeout: float = 1.0) -> Optional[SQLiteTask]:
        """从队列获取任务（阻塞式）"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.lock:
                task = self._get_pending_task(task_type)
                if task:
                    # 标记为处理中
                    task.status = TaskStatus.PROCESSING.value
                    task.updated_at = time.time()
                    self.put(task)
                    return task

            time.sleep(0.1)  # 短暂等待

        return None

    def _get_pending_task(self, task_type: Optional[str] = None) -> Optional[SQLiteTask]:
        """获取待处理任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = '''
                    SELECT * FROM tasks
                    WHERE status = ?
                '''
                params = [TaskStatus.PENDING.value]

                if task_type:
                    query += ' AND task_type = ?'
                    params.append(task_type)

                query += ' ORDER BY priority DESC, created_at ASC LIMIT 1'

                row = conn.execute(query, params).fetchone()
                if row:
                    return SQLiteTask(
                        task_id=row['task_id'],
                        task_type=row['task_type'],
                        data=json.loads(row['data']),
                        status=row['status'],
                        priority=row['priority'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        result=json.loads(row['result']) if row['result'] else None,
                        error=row['error']
                    )
        except Exception as e:
            print(f"获取任务失败: {e}")

        return None

    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """标记任务完成"""
        return self._update_task_status(task_id, TaskStatus.COMPLETED, result=result)

    def fail_task(self, task_id: str, error: str) -> bool:
        """标记任务失败"""
        return self._update_task_status(task_id, TaskStatus.FAILED, error=error)

    def _update_task_status(self, task_id: str, status: TaskStatus,
                           result: Optional[Dict[str, Any]] = None,
                           error: Optional[str] = None) -> bool:
        """更新任务状态"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        UPDATE tasks
                        SET status = ?, updated_at = ?, result = ?, error = ?
                        WHERE task_id = ?
                    ''', (
                        status.value,
                        time.time(),
                        json.dumps(result) if result else None,
                        error,
                        task_id
                    ))
                    conn.commit()
                    return conn.total_changes > 0
            except Exception as e:
                print(f"更新任务状态失败: {e}")
                return False

    def get_statistics(self) -> Dict[str, int]:
        """获取队列统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                for status in TaskStatus:
                    count = conn.execute(
                        'SELECT COUNT(*) FROM tasks WHERE status = ?',
                        [status.value]
                    ).fetchone()[0]
                    stats[status.value] = count
                return stats
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}

    def clear_completed(self, older_than: int = 3600) -> int:
        """清理已完成的旧任务（默认1小时前）"""
        cutoff_time = time.time() - older_than
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('''
                        DELETE FROM tasks
                        WHERE status IN (?, ?) AND updated_at < ?
                    ''', [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, cutoff_time])
                    conn.commit()
                    return cursor.rowcount
            except Exception as e:
                print(f"清理任务失败: {e}")
                return 0

    def get_pending_tasks(self, task_type: Optional[str] = None) -> List[SQLiteTask]:
        """获取所有待处理任务（用于调试）"""
        tasks = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = 'SELECT * FROM tasks WHERE status = ?'
                params = [TaskStatus.PENDING.value]

                if task_type:
                    query += ' AND task_type = ?'
                    params.append(task_type)

                query += ' ORDER BY priority DESC, created_at ASC'

                rows = conn.execute(query, params).fetchall()
                for row in rows:
                    tasks.append(SQLiteTask(
                        task_id=row['task_id'],
                        task_type=row['task_type'],
                        data=json.loads(row['data']),
                        status=row['status'],
                        priority=row['priority'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        result=json.loads(row['result']) if row['result'] else None,
                        error=row['error']
                    ))
        except Exception as e:
            print(f"获取待处理任务失败: {e}")

        return tasks

# 使用示例
if __name__ == "__main__":
    # 创建任务队列
    queue = SQLiteTaskQueue("test_tasks.db")

    # 添加任务
    task = SQLiteTask(
        task_id=str(uuid.uuid4()),
        task_type=TaskType.RECOGNITION.value,
        data={"audio_data": "mock_audio", "record_id": "test_001"},
        priority=1
    )
    queue.put(task)
    print(f"添加任务: {task.task_id}")

    # 获取任务
    pending_task = queue.get(task_type=TaskType.RECOGNITION.value)
    if pending_task:
        print(f"获取到任务: {pending_task.task_id}")

        # 模拟处理完成
        result = {"text": "识别结果", "confidence": 0.95}
        queue.complete_task(pending_task.task_id, result)
        print("任务完成")

    # 查看统计
    stats = queue.get_statistics()
    print(f"队列统计: {stats}")