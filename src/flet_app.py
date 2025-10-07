#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DouDou - Flet 原型应用
基于 Flet 的现代化语音转文字应用
"""

import os
import time
import flet as ft
from typing import Optional

# 首先导入并初始化日志系统
from utils.logger import get_logger
logger = get_logger()

from core import (
    AudioEngine,
    AudioRecorder,
    TranscriptionHandler,
    RecognitionPipeline,
    AIProcessor,
    HybridVADSegmenter,
    VADConfig,
    create_chinese_optimized_config,
    TaskManager,
    ContinuousAudioRecorder,
    RecorderConfig,
    AudioSegment,
)
from utils.config_manager import ConfigManager
from ui.dialogs import create_settings_dialog, HelpDialog
from ui.components import (
    RecordButton,
    StatusDisplay,
    AudioVisualization,
    ResultCard,
    AudioDeviceSelector,
    RealtimeModeToggle,
    ActionButtons,
)
from ui.task_monitor import TaskMonitor


class QuQuFletApp:
    """DouDou Flet应用主类 - 协调器模式"""

    def __init__(self, page: ft.Page):
        self.page = page
        self._setup_page()
        self._init_services()
        self._setup_ui()
        self._setup_callbacks()

        # 设置页面关闭时的清理
        page.on_close = self._on_page_close

        # UI 调度器：确保所有UI更新在主线程执行
        # 使用 page.invoke_later 将函数投递到UI线程执行
        # 仅在回调/后台线程中使用，避免线程安全问题
        
    def _dispatch_ui(self, fn, *args, **kwargs):
        """将UI更新安全调度到主线程执行"""
        try:
            from functools import partial
            import threading

            # 检查是否在主线程中（Flet的UI线程）
            main_thread = getattr(self, '_main_thread', None)
            if main_thread is None:
                # 首次调用时记录主线程
                self._main_thread = threading.current_thread()
                main_thread = self._main_thread

            current_thread = threading.current_thread()

            # 如果已经在主线程中，直接执行
            if current_thread == main_thread:
                fn(*args, **kwargs)
                return

            # 如果不在主线程，使用invoke_later调度
            if hasattr(self.page, "invoke_later") and callable(self.page.invoke_later):
                self.page.invoke_later(partial(fn, *args, **kwargs))
            else:
                # 回退方案：直接执行并尝试更新（正常行为，无需警告）
                # logger.debug("invoke_later不可用，直接执行UI更新")
                fn(*args, **kwargs)
                try:
                    if self.page:
                        self.page.update()
                except Exception as update_error:
                    logger.warning(f"UI更新失败: {update_error}")

        except Exception as e:
            logger.error(f"UI调度失败: {type(e).__name__}: {e}")
            # 最后的保险：尝试直接执行
            try:
                fn(*args, **kwargs)
            except Exception as direct_error:
                logger.error(f"直接执行UI更新也失败: {type(direct_error).__name__}: {direct_error}")

    def _on_page_close(self):
        """页面关闭时的清理工作"""
        try:
            print("[INFO] 正在清理应用资源...")

            # 停止连续录音
            if hasattr(self, 'continuous_recorder') and self.continuous_recorder:
                self.continuous_recorder.stop_continuous_recording()

            # 停止任务管理器
            if hasattr(self, 'task_manager') and self.task_manager:
                self.task_manager.stop()

            # 停止任务监控
            if hasattr(self, 'task_monitor') and self.task_monitor:
                self.task_monitor.stop_monitoring()

            print("[INFO] 应用资源清理完成")
        except Exception as e:
            print(f"[ERROR] 清理资源时出错: {e}")

    def _setup_page(self):
        """设置页面基本属性"""
        self.page.title = "DouDou - 智能语音助手"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # 窗口设置
        self.page.window.width = 1200
        self.page.window.height = 700
        self.page.window.min_width = 1000
        self.page.window.min_height = 600
        self.page.window.resizable = True

        # 设置图标
        icon_ico_path = "assets/icon.ico"
        icon_png_path = "assets/icon.png"
        if os.path.exists(icon_ico_path):
            self.page.window.icon = icon_ico_path
        elif os.path.exists(icon_png_path):
            self.page.window.icon = icon_png_path

    def _init_services(self):
        """初始化核心服务"""
        # 配置管理
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.get_all()

        # 音频引擎
        try:
            self.audio_engine = AudioEngine(sample_rate=16000, chunk_size=1024, channels=1)
            self.audio_engine.initialise()
            print("[INFO] 音频引擎初始化成功")
        except Exception as e:
            print(f"[ERROR] 音频引擎初始化失败: {e}")
            self.audio_engine = None
            self.audio_disabled_mode = True

        # 录音管理器
        self.audio_recorder = AudioRecorder(self.audio_engine)

        # 识别流水线 - 使用直接集成模式
        self.recognition_pipeline = RecognitionPipeline(use_direct_integration=True)

        # AI处理器
        self.ai_processor = None
        if self.settings.get("enable_ai_optimization", False):
            # 从ai_services.default中读取AI配置
            ai_services = self.settings.get("ai_services", {})
            default_config = ai_services.get("default", {})

            self.ai_processor = AIProcessor(
                api_key=default_config.get("api_key", ""),
                base_url=default_config.get("base_url", ""),
                model_name=default_config.get("model_name", "")
            )

        # 转写处理器
        self.transcription_handler = TranscriptionHandler(
            recognition_pipeline=self.recognition_pipeline,
            ai_processor=self.ai_processor
        )

        # VAD分段器 - 使用中文语音优化配置
        self.vad_config = create_chinese_optimized_config()
        self.vad_segmenter = HybridVADSegmenter(sample_rate=16000, config=self.vad_config)

        # 多线程任务管理器
        # 使用新的统一任务系统
        funasr_recognizer = self.recognition_pipeline.direct_funasr if self.recognition_pipeline.use_direct_integration else None
        from core.task_adapter import create_task_manager
        # 使用旧任务管理器（实现主线+并行任务池架构）
        self.task_manager = create_task_manager(
            use_unified_system=False,
            funasr_recognizer=funasr_recognizer,
            config_manager=self.config_manager
        )

        # 尝试启动TaskManager，如果失败则记录但不阻止应用启动
        try:
            self.task_manager.start()
            logger.info("新任务系统启动成功")
            print("[INFO] 已启用新的统一任务系统，解决AI任务阻塞问题")
        except Exception as e:
            logger.error(f"任务系统启动失败: {e}")
            print(f"[WARNING] 任务系统启动失败，某些功能可能不可用: {e}")
            # 不阻止应用启动，继续初始化其他组件

        # 连续录音器 - 用于实时模式
        recorder_config = RecorderConfig(
            sample_rate=16000,
            channels=1,
            chunk_size=1024,
            min_segment_duration=0.5,
            max_segment_duration=8.0,
            silence_timeout=1.5,
        )
        self.continuous_recorder = ContinuousAudioRecorder(
            audio_engine=self.audio_engine,
            vad_segmenter=self.vad_segmenter,
            task_manager=self.task_manager,
            config=recorder_config
        )

        # 设置任务管理器回调
        self.task_manager.on_recognition_complete = self._on_recognition_complete
        self.task_manager.on_correction_complete = self._on_correction_complete
        self.task_manager.on_translation_complete = self._on_translation_complete
        self.task_manager.on_ui_update = self._on_ui_update
        self.task_manager.on_statistics_update = self._on_statistics_update

        # 设置连续录音器回调
        self.continuous_recorder.on_segment_detected = self._on_audio_segment_detected
        self.continuous_recorder.on_recording_started = self.on_recording_started
        self.continuous_recorder.on_recording_stopped = lambda: self.on_continuous_recording_stopped()
        self.continuous_recorder.on_error = self._on_recorder_error

    def _setup_ui(self):
        """设置UI界面"""
        # 顶部标题
        self.header = ft.Column(
            [
                ft.Text(
                    "🎤 DouDou",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700,
                ),
                ft.Text(
                    "开源免费的智能语音助手",
                    size=14,
                    color=ft.Colors.GREY_600,
                ),
                ft.Divider(height=15),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 录音控制区域 - 用容器包装以便更新
        self.record_button_container = ft.Container()
        self.record_button = RecordButton(on_click=self.toggle_recording)
        self.record_button.set_parent_container(self.record_button_container)
        self.record_button_container.content = self.record_button.button

        self.status_display = StatusDisplay()

        self.audio_visualization = AudioVisualization()

        self.audio_device_selector = AudioDeviceSelector(
            audio_engine=self.audio_engine,
            on_device_change=self.on_audio_device_change
        )

        # 初始化按钮状态（根据设备可用性）
        self._update_record_button_state()

        # 实时模式切换
        self.realtime_toggle = RealtimeModeToggle(
            on_change=self.toggle_realtime_mode
        )

        # 翻译开关
        self.translation_switch = ft.Switch(
            label="启用翻译",
            value=self.settings.get("enable_translation", False),
            on_change=self.toggle_translation,
            disabled=False
        )

        # 结果显示区域
        self.result_card = ResultCard()

        # 操作按钮组
        self.action_buttons = ActionButtons(
            on_copy=self.copy_result,
            on_export=self.export_result,
            on_clear=self.clear_result,
            on_optimize=self.summarize_results
        )

        # 设备状态显示
        self.device_status_text = ft.Text(
            "音频设备: 默认设备 | 计算设备: 检测中...",
            size=12,
            color=ft.Colors.GREY_600,
            italic=True,
        )

        # 设置按钮
        self.settings_button = ft.ElevatedButton(
            text="设置",
            icon=ft.Icons.SETTINGS,
            on_click=self.open_settings,
            width=85,
            height=32,
        )

        self.help_button = ft.ElevatedButton(
            text="帮助",
            icon=ft.Icons.HELP,
            on_click=self.open_help,
            width=85,
            height=32,
        )

        # 任务监控器
        self.task_monitor = TaskMonitor(self.task_manager)

        # 主界面布局
        self.main_layout = self._build_main_layout()
        self.page.add(self.main_layout)

        # 初始化设备状态显示（必须在UI创建之后）
        self.update_device_status(None)

        # 恢复上次选择的音频设备
        self._restore_last_audio_device()

        # 启动任务监控
        self.task_monitor.start_monitoring()

        # 预加载FunASR模型（UI初始化完成后，启动时加载一次，后续复用）
        if self.recognition_pipeline.use_direct_integration and self.recognition_pipeline.direct_funasr:
            self._initialize_funasr_models()

    def _build_main_layout(self) -> ft.Control:
        """构建主界面布局"""
        # 左侧控制面板
        left_panel = ft.Container(
            width=300,
            padding=ft.padding.all(15),
            content=ft.Column([
                self.header,
                ft.Container(height=15),
                # 录音控制区域 - 录音按钮
                self.record_button_container,
                ft.Container(height=8),
                # 实时模式切换 - 放在录音按钮下方
                ft.Row([
                    ft.Container(width=15),  # 左边距
                    self.realtime_toggle.switch,
                    ft.Container(width=15),  # 右边距
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=8),
                # 翻译开关
                ft.Row([
                    ft.Container(width=15),  # 左边距
                    self.translation_switch,
                    ft.Container(width=15),  # 右边距
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=12),
                self.status_display.status_text,
                ft.Container(height=12),
                self.audio_visualization.container,
                ft.Container(height=15),
                self.audio_device_selector.control,
                ft.Container(height=15),
                ft.Row([
                    self.settings_button,
                    ft.Container(width=8),
                    self.help_button,
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )

        # 中间面板（识别结果）
        middle_panel = ft.Container(
            expand=2,  # 占2份空间
            padding=ft.padding.all(15),
            content=ft.Column([
                # 设备信息区域
                ft.Container(
                    content=ft.Row([
                        self.device_status_text,
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=ft.padding.only(bottom=10),
                ),
                # 识别结果区域（占满剩余空间）
                ft.Container(
                    expand=True,
                    content=self.result_card.card
                ),
                # 操作按钮区域
                ft.Container(
                    content=self.action_buttons.get_control(),
                    padding=ft.padding.only(top=10),
                ),
            ]),
        )

        # 右侧面板（任务监控）
        right_panel = ft.Container(
            width=280,  # 固定宽度
            padding=ft.padding.all(15),
            content=self.task_monitor.get_control(),
        )

        return ft.Row([
            left_panel,
            ft.VerticalDivider(width=1),
            middle_panel,
            ft.VerticalDivider(width=1),
            right_panel,
        ], expand=True)

    def _setup_callbacks(self):
        """设置回调函数"""
        # 录音回调
        self.audio_recorder.on_recording_started = self.on_recording_started
        self.audio_recorder.on_recording_stopped = self.on_recording_stopped
        self.audio_recorder.on_audio_level_update = self.update_audio_level
        self.audio_recorder.on_status_update = self.update_status

        # 转写回调
        self.transcription_handler.on_transcription_complete = self.on_transcription_complete
        self.transcription_handler.on_status_update = self.update_status
        self.transcription_handler.on_ai_optimization_complete = self.on_ai_optimization_complete
        self.transcription_handler.get_context_history = self.get_context_history

        # VAD回调
        self.vad_segmenter.on_segment_detected = self.on_vad_segment_detected

    # 录音控制
    def toggle_recording(self, e=None):
        """切换录音状态"""
        if not self.audio_engine:
            self.update_status("音频引擎未初始化，请检查音频设备")
            return

        # 根据实时模式选择不同的录音方式
        if self.realtime_toggle.is_realtime:
            # 实时模式：使用连续录音器（VAD自动分段+实时识别）
            if self.continuous_recorder.is_recording:
                self.continuous_recorder.stop_continuous_recording()
            else:
                success = self.continuous_recorder.start_continuous_recording()
                if not success:
                    self.update_status("启动实时录音失败")
                    self.realtime_toggle.set_realtime(False)
        else:
            # 普通模式：使用标准录音器（手动开始/停止）
            if self.audio_recorder.is_recording:
                self.audio_recorder.stop_recording()
            else:
                from core.audio_engine import AudioStreamConfig
                stream_config = AudioStreamConfig(
                    format=self.audio_engine.audio_format,
                    channels=self.audio_engine.channels,
                    rate=self.audio_engine.sample_rate,
                    chunk=self.audio_engine.chunk_size,
                    device_index=self.audio_recorder.device_index
                )
                self.audio_recorder.start_recording(stream_config)

    def on_recording_started(self):
        """录音开始回调"""
        self.record_button.set_recording_state(True)
        self.audio_visualization.set_recording(True)
        self.update_status("正在录音...")
        self.page.update()

    def on_recording_stopped(self, audio_file: str):
        """录音停止回调（普通模式）"""
        print(f"[DEBUG] 录音停止回调触发，音频文件: {audio_file}")
        self.record_button.set_recording_state(False)
        self.audio_visualization.set_recording(False)
        self.update_status("录音完成")
        self.page.update()

        # 开始转写（使用统一任务系统）
        if audio_file:
            print(f"[DEBUG] 开始转写音频文件: {audio_file}")
            # 先添加一个占位符识别结果来获取record_id
            record_id = self.result_card.add_recognition_result("正在识别...")

            # 使用旧TaskManager提交识别任务
            if hasattr(self.task_manager, 'submit_recognition_task'):
                from core.task_manager import RecognitionTask, TaskPriority

                # 获取音频时长
                try:
                    import librosa
                    duration = librosa.get_duration(filename=audio_file)
                except:
                    duration = 0.0

                # 创建音频片段
                audio_segment = AudioSegment(
                    file_path=audio_file,
                    timestamp=time.time(),
                    duration=duration,
                    segment_id=f"seg_{int(time.time() * 1000)}",
                    vad_confidence=0.8,
                    sample_rate=16000,
                    channels=1
                )

                # 创建识别任务
                recognition_task = RecognitionTask(
                    audio_segment=audio_segment,
                    task_id=f"task_{int(time.time() * 1000)}",
                    created_at=time.time(),
                    priority=TaskPriority.NORMAL,
                    record_id=record_id
                )

                # 提交到旧TaskManager
                task_id = self.task_manager.submit_recognition_task(recognition_task)
                print(f"[DEBUG] 已提交识别任务到任务池: {task_id}")
            else:
                # 回退到旧的转录处理器
                print(f"[DEBUG] 回退到旧的转录处理器")
                self.transcription_handler.transcribe_audio_file(
                    audio_file,
                    enable_ai_optimization=self.settings.get("enable_ai_optimization", False)
                )
        else:
            print(f"[DEBUG] 没有音频文件，跳过转写")

    def on_continuous_recording_stopped(self):
        """连续录音停止回调（实时模式）"""
        print(f"[DEBUG] 连续录音停止")
        self.record_button.set_recording_state(False)
        self.audio_visualization.set_recording(False)
        self.update_status("实时录音已停止")
        self.page.update()

    def update_audio_level(self, level: float):
        """更新音频级别显示"""
        self.audio_visualization.update("🎤 正在录音", level)

    def update_status(self, message: str):
        """更新状态显示"""
        def _do():
            self.status_display.update_status(message)
            if self.page:
                self.page.update()
        self._dispatch_ui(_do)

    # 转写处理
    def on_transcription_complete(self, result: dict):
        """转写完成回调"""
        print(f"[DEBUG] 转写完成回调触发，结果: {result}")
        if result.get("success"):
            text = result.get("text", "")
            print(f"[DEBUG] 转写成功，文本: {text[:100]}...")
            # 添加新的识别记录，包含原文
            record_id = self.result_card.add_recognition_result(text)
            print(f"[DEBUG] 添加识别记录，ID: {record_id}")
            self.update_status("转写完成")
        else:
            error = result.get("error", "转写失败")
            print(f"[DEBUG] 转写失败，错误: {error}")
            self.update_status(f"转写失败: {error}")
        self.page.update()

    def on_ai_optimization_complete(self, optimized_text: str):
        """AI优化完成回调"""
        # 智能提取修正结果，过滤掉思考内容和分析过程
        filtered_text = self._extract_correction_result(optimized_text)
        # 更新最近的识别记录，添加修正文本
        success = self.result_card.update_latest_correction(filtered_text)
        if success:
            print(f"[DEBUG] 更新修正文本成功: {filtered_text[:50]}...")
        else:
            print(f"[DEBUG] 没有找到可更新的识别记录，添加为新记录")
            self.result_card.add_recognition_result(filtered_text)
        self.page.update()

    # 设备管理
    def _filter_ai_thinking_content(self, text: str) -> str:
        """过滤AI回答中的思考内容，去除思考标记和前后空格换行"""
        import re

        # 去除思考内容标记，如 <think> ... </think> 或类似的思考过程
        # 支持多种思考标记格式
        thinking_patterns = [
            r'<think>.*?</think>',  # <think>...</think>
            r'<思考>.*?</思考>',    # <思考>...</思考>
            r'<thinking>.*?</thinking>',  # <thinking>...</thinking>
            r'<reasoning>.*?</reasoning>', # <reasoning>...</reasoning>
            r'<analysis>.*?</analysis>',   # <analysis>...</analysis>
            r'<step>.*?</step>',           # <step>...</step>
            r'<process>.*?</process>',     # <process>...</process>
        ]

        filtered_text = text
        for pattern in thinking_patterns:
            filtered_text = re.sub(pattern, '', filtered_text, flags=re.DOTALL | re.IGNORECASE)

        # 去除前后多余的空格和换行
        filtered_text = filtered_text.strip()

        # 去除可能的多余空行
        filtered_text = re.sub(r'\n\s*\n', '\n', filtered_text)

        # 去除行首行尾空格
        filtered_text = '\n'.join(line.strip() for line in filtered_text.split('\n'))

        return filtered_text

    def _extract_translation_result(self, text: str) -> str:
        """智能提取翻译结果，过滤掉对话过程、思考内容和多余信息"""
        import re

        # 首先应用基本的思考内容过滤
        text = self._filter_ai_thinking_content(text)

        # 移除对话式的交互内容
        conversation_patterns = [
            r'好的，用户让我.*?需要：',  # 开头的理解性话语
            r'首先，检查.*?接下来，',   # 分析过程描述
            r'然后，确保.*?最后，',     # 步骤描述
            r'接下来，.*?最终，',       # 过程描述
            r'我需要.*?我会：',         # 自我描述
            r'让我.*?我应该：',         # 思考过程
            r'原文是：.*?译文是：',     # 直接的翻译说明
            r'源语言：.*?目标语言：',   # 语言标签
            r'需要翻译的文本：',        # 翻译任务说明
            r'请将.*?翻译成',           # 翻译指令
            r'以下是翻译结果：',        # 结果引导语
            r'(翻译完成|Translation complete|日語に翻訳完成)',  # 完成标记
            r'注意：.*?另外：',         # 补充说明
            r'解释：.*?说明：',         # 解释性内容
            r'目标语言：',             # 语言标签
            r'Assistant:.*?需要翻译的文本：',  # Assistant格式的任务描述
            r'Human:.*?翻译后的文本：',  # Human格式的结果标记
            r'输出：',                 # 输出标记
        ]

        cleaned_text = text
        for pattern in conversation_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)

        # 移除括号中的说明性文字（中文和英文）
        explanation_patterns = [
            r'\([^)]*解释[^)]*\)',      # 包含"解释"的括号
            r'\([^)]*说明[^)]*\)',      # 包含"说明"的括号
            r'\([^)]*注[^)]*\)',         # 包含"注"的括号
            r'\([^)]*note[^)]*\)',      # 包含"note"的括号
            r'\（[^）]*解释[^）]*\）',    # 中文括号的解释
            r'\（[^）]*说明[^）]*\）',    # 中文括号的说明
        ]

        for pattern in explanation_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)

        # 移除常见的连接词和过渡语
        transition_patterns = [
            r'^(好的|嗯|那么|接下来|然后|另外|此外|还有|同时)\s*[，：。]',
            r'\s+(好的|嗯|那么|接下来|然后|另外|此外|还有|同时)\s*[，：。]',
            r'^(首先|其次|最后|最终|总之|总结)\s*[，：。]',
            r'\s+(首先|其次|最后|最终|总之|总结)\s*[，：。]',
        ]

        for pattern in transition_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)

        # 移除重复的标点符号
        cleaned_text = re.sub(r'[，。！？]{2,}', lambda m: m.group(0)[0], cleaned_text)
        cleaned_text = re.sub(r'[，。！？]\s*[，。！？]', lambda m: m.group(0)[0], cleaned_text)

        # 智能提取翻译结果 - 寻找最可能的翻译内容
        lines = cleaned_text.split('\n')
        translation_candidates = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过明显的非翻译内容
            skip_patterns = [
                r'^(Human|Assistant|User|AI):',  # 对话标签
                r'^\d+\.',                      # 数字列表
                r'^[一二三四五六七八九十]+[、.]',  # 中文数字列表
                r'^[•\-\*]\s',                  # 项目符号
                r'^(要求|注意|说明|解释):',      # 说明性文字开头
                r'^(请|需要|应该|必须)',          # 指令性文字开头
                r'(翻译|translate|translation)', # 包含翻译相关词汇
                r'(检查|确保|保持|符合)',         # 包含检查相关词汇
                r'需要翻译的文本：',              # 任务描述
                r'翻译后的文本：',                # 结果标记
                r'目标语言：',                    # 语言标签
                r'^「',                         # 中文引号开头（通常是原文）
                r'^（注：',                      # 注释开头
                r'^\(注：',                      # 英文注释开头
            ]

            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    should_skip = True
                    break

            if not should_skip and len(line) > 5:  # 过短的行很可能是噪音
                translation_candidates.append(line)

        # 特殊处理：如果有多行文本，尝试提取最可能的翻译结果
        if len(translation_candidates) > 1:
            # 查找包含引号的行（可能是直接翻译结果）
            quoted_candidates = []
            for candidate in translation_candidates:
                if (candidate.startswith('「') and candidate.endswith('」')) or \
                   (candidate.startswith('"') and candidate.endswith('"')) or \
                   (candidate.startswith('"') and candidate.endswith('"')):
                    quoted_candidates.append(candidate)

            if quoted_candidates:
                translation_candidates = quoted_candidates

        # 如果还是没有找到合适的候选，尝试更智能的模式匹配
        if not translation_candidates:
            # 使用正则表达式直接提取翻译结果
            translation_patterns = [
                r'「([^」]+)」',                    # 中文引号内容
                r'"([^"]+)"',                     # 英文引号内容
                r'"([^"]+)"',                     # 中文引号内容
                r'翻译后的文本[:：]\s*(.+)',        # "翻译后的文本："格式
                r'Assistant[:：]\s*(.+)',          # Assistant: 后的内容
                r'输出[:：]\s*(.+)',               # "输出："格式
                r'(?:翻译|译文)[:：]\s*(.+)',      # "翻译/译文："格式
            ]

            for pattern in translation_patterns:
                matches = re.findall(pattern, cleaned_text, re.MULTILINE | re.DOTALL)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    if match and len(match.strip()) > 5:
                        translation_candidates.append(match.strip())

        # 如果有候选行，选择最合适的
        if translation_candidates:
            # 优先选择包含目标语言特征的行
            target_language_patterns = {
                'ja': r'[ひらがなカタカナ漢字]',  # 日语字符
                'en': r'[a-zA-Z]',                # 英文字符
                'ko': r'[가-힣]',                  # 韩语字符
                'fr': r'[àâäçéèêëïîôöùûüÿ]',      # 法语特殊字符
                'de': r'[äöüß]',                  # 德语特殊字符
                'ru': r'[а-яё]',                  # 俄语字符
                'es': r'[ñáéíóúü]',               # 西班牙语特殊字符
            }

            # 尝试从配置获取目标语言，默认为日语
            target_lang = self.settings.get('ai_services', {}).get('translation', {}).get('target_language', 'ja')

            scored_candidates = []
            for candidate in translation_candidates:
                score = 0

                # 检查是否包含目标语言字符
                if target_lang in target_language_patterns:
                    if re.search(target_language_patterns[target_lang], candidate):
                        score += 10

                # 检查句子完整性（以句号、问号、感叹号结尾）
                if re.search(r'[。！？.!?]$', candidate):
                    score += 5

                # 检查长度适中性
                if 10 <= len(candidate) <= 200:
                    score += 3

                # 检查是否包含中文（如果是翻译成外语，应该较少中文）
                if re.search(r'[\u4e00-\u9fff]', candidate) and target_lang != 'zh':
                    score -= 2

                scored_candidates.append((score, candidate))

            # 选择得分最高的候选
            if scored_candidates:
                scored_candidates.sort(key=lambda x: x[0], reverse=True)
                return scored_candidates[0][1]

        # 如果没有找到合适的候选，返回清理后的文本
        return cleaned_text.strip()

    def _extract_correction_result(self, text: str) -> str:
        """智能提取修正结果，过滤掉思考内容和多余信息"""
        import re

        # 首先应用基本的思考内容过滤
        text = self._filter_ai_thinking_content(text)

        # 移除修正过程的分析性内容
        analysis_patterns = [
            r'好的，用户让我.*?需要：',           # 开头的理解性话语
            r'首先，检查.*?接下来，',             # 分析过程描述
            r'然后，确保.*?最后，',               # 步骤描述
            r'我需要.*?我会：',                   # 自我描述
            r'让我.*?我应该：',                   # 思考过程
            r'分析：.*?结论：',                   # 分析框架
            r'检查：.*?修正：',                   # 检查过程
            r'问题：.*?解决：',                   # 问题解决描述
            r'发现.*?改进：',                     # 改进过程描述
            r'以下是修正后的文本：',              # 结果引导语
            r'(修正完成|优化完成)',               # 完成标记
        ]

        cleaned_text = text
        for pattern in analysis_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)

        # 移除括号中的说明性文字
        explanation_patterns = [
            r'\([^)]*解释[^)]*\)',              # 包含"解释"的括号
            r'\([^)]*说明[^)]*\)',              # 包含"说明"的括号
            r'\([^)]*分析[^)]*\)',              # 包含"分析"的括号
            r'\([^)]*理由[^)]*\)',              # 包含"理由"的括号
            r'\（[^）]*解释[^）]*\）',            # 中文括号的解释
            r'\（[^）]*说明[^）]*\）',            # 中文括号的说明
        ]

        for pattern in explanation_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)

        # 移除常见的连接词和过渡语
        transition_patterns = [
            r'^(好的|嗯|那么|接下来|然后|另外|此外|还有|同时)\s*[，：。]',
            r'\s+(好的|嗯|那么|接下来|然后|另外|此外|还有|同时)\s*[，：。]',
            r'^(首先|其次|最后|最终|总之|总结)\s*[，：。]',
            r'\s+(首先|其次|最后|最终|总之|总结)\s*[，：。]',
        ]

        for pattern in transition_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)

        # 智能提取修正结果 - 寻找最可能的修正内容
        lines = cleaned_text.split('\n')
        correction_candidates = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过明显的非修正内容
            skip_patterns = [
                r'^(Human|Assistant|User|AI):',    # 对话标签
                r'^\d+\.',                          # 数字列表
                r'^[一二三四五六七八九十]+[、.]',      # 中文数字列表
                r'^[•\-\*]\s',                      # 项目符号
                r'^(要求|注意|说明|解释|分析):',      # 说明性文字开头
                r'^(请|需要|应该|必须|检查|确保)',     # 指令性文字开头
                r'(修正|优化|改进|纠正|调整)',         # 包含修正相关词汇
                r'(检查|确保|保持|符合|验证)',         # 包含检查相关词汇
                r'(原文|原始|初始)',                   # 包含原文相关词汇
            ]

            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    should_skip = True
                    break

            if not should_skip and len(line) > 5:  # 过短的行很可能是噪音
                correction_candidates.append(line)

        # 如果有候选行，选择最合适的
        if correction_candidates:
            scored_candidates = []
            for candidate in correction_candidates:
                score = 0

                # 检查句子完整性（以句号、问号、感叹号结尾）
                if re.search(r'[。！？.!?]$', candidate):
                    score += 5

                # 检查长度适中性
                if 8 <= len(candidate) <= 300:
                    score += 3

                # 检查是否包含中文（修正结果应该是中文）
                if re.search(r'[\u4e00-\u9fff]', candidate):
                    score += 10

                # 检查标点符号使用（好的中文文本应该有适当标点）
                if re.search(r'[，。！？；：]', candidate):
                    score += 2

                # 减分项：包含明显的分析性词汇
                if re.search(r'(分析|检查|发现|问题|解决|改进|优化)', candidate):
                    score -= 3

                scored_candidates.append((score, candidate))

            # 选择得分最高的候选
            if scored_candidates:
                scored_candidates.sort(key=lambda x: x[0], reverse=True)
                return scored_candidates[0][1]

        # 如果没有找到合适的候选，返回清理后的文本
        return cleaned_text.strip()

    # 设备管理
    def on_audio_device_change(self, device_index: Optional[int]):
        """音频设备变更回调"""
        self.audio_recorder.set_device(device_index)
        # 更新设备状态显示
        self.update_device_status(device_index)
        # 更新录音按钮状态（有设备才能录音）
        self._update_record_button_state()

        # 保存设备选择到配置
        if device_index is not None:
            device_name = self.audio_recorder.get_device_name(device_index)
            self.settings["last_audio_device_index"] = device_index
            self.settings["last_audio_device_name"] = device_name
            self.config_manager.set("last_audio_device_index", device_index)
            self.config_manager.set("last_audio_device_name", device_name)
            self.config_manager.save()
            print(f"[INFO] 已保存音频设备: {device_name} (索引: {device_index})")

    def update_device_status(self, device_index: Optional[int]):
        """更新设备状态显示"""
        try:
            if device_index is None:
                device_name = "默认设备"
            else:
                device_name = self.audio_recorder.get_device_name(device_index)

            # 保留计算设备信息
            compute_device = self.device_status_text.value.split("|")[1].strip() if "|" in self.device_status_text.value else "计算设备: 检测中..."
            self.device_status_text.value = f"音频设备: {device_name} | {compute_device}"
            self.page.update()
        except Exception as e:
            print(f"[DEBUG] 更新设备状态失败: {e}")
            compute_device = self.device_status_text.value.split("|")[1].strip() if "|" in self.device_status_text.value else "计算设备: 检测中..."
            self.device_status_text.value = f"音频设备: 未知设备 | {compute_device}"
            self.page.update()

    def _update_record_button_state(self):
        """更新录音按钮状态（根据设备选择）"""
        # 检查是否有可用设备
        has_options = len(self.audio_device_selector.dropdown.options) > 0

        # 如果有可用设备但未选择，禁用按钮
        if has_options:
            has_selected = self.audio_device_selector.dropdown.value is not None
            self.record_button.button.disabled = not has_selected
        else:
            # 没有可用设备，禁用按钮
            self.record_button.button.disabled = True

        if self.page:
            self.page.update()

    # 实时模式
    def toggle_realtime_mode(self, is_realtime: bool):
        """切换实时模式"""
        if is_realtime:
            # 只是切换模式，不自动开始录音
            self.update_status("实时模式已开启（点击'开始录音'以启动）")
        else:
            # 如果正在录音，停止连续录音
            if self.continuous_recorder.is_recording:
                try:
                    self.continuous_recorder.stop_continuous_recording()
                    self.update_status("实时模式已关闭")
                    self.record_button.set_recording_state(False)
                except Exception as e:
                    print(f"[ERROR] 停止连续录音失败: {e}")
                    self.update_status(f"停止实时模式失败: {e}")
            else:
                self.update_status("实时模式已关闭")

    def toggle_translation(self, e=None):
        """切换翻译功能"""
        is_enabled = self.translation_switch.value
        self.config_manager.set("enable_translation", is_enabled)
        self.config_manager.save()

        if is_enabled:
            self.update_status("翻译功能已开启")
        else:
            self.update_status("翻译功能已关闭")

    def on_vad_segment_detected(self, segment):
        """VAD段落检测回调（旧的，保留兼容性）"""
        if self.realtime_toggle.is_realtime:
            self.update_status("检测到语音，正在处理...")

    # TaskManager 回调方法
    def _on_audio_segment_detected(self, audio_segment: AudioSegment):
        """音频片段检测回调"""
        print(f"[DEBUG] 检测到音频片段: {audio_segment.segment_id}, 时长: {audio_segment.duration:.2f}s")

        # 使用新的统一任务系统，直接提交完整任务
        if hasattr(self, 'task_manager') and self.task_manager:
            try:
                # 统一调用 submit_audio_segment，原TaskManager/适配器均支持
                fut = self.task_manager.submit_audio_segment(audio_segment)
                logger.info(f"提交音频任务: {getattr(fut, 'task_id', 'future')} ")
            except Exception as e:
                logger.error(f"提交音频任务失败: {e}")
                self.update_status(f"任务提交失败: {str(e)}")

    def _on_recognition_complete(self, task):
        """语音识别完成回调"""
        if task.result and task.result.get('success'):
            text = task.result.get('text', '')
            confidence = task.result.get('confidence', 0)
            print(f"[DEBUG] 识别完成: {text} (置信度: {confidence:.3f})")

            # 预生成 record_id 并绑定到任务（避免跨线程取返回值）
            import time as _time
            record_id = f"record_{int(_time.time()*1000)}"
            try:
                if hasattr(self, 'task_manager') and hasattr(task, 'task_id'):
                    if hasattr(self.task_manager, 'bind_record_id'):
                        self.task_manager.bind_record_id(task.task_id, record_id)
            except Exception as e:
                logger.warning(f"绑定record_id失败: {e}")

            # 在UI线程添加记录与更新
            def _ui_add_recognition():
                try:
                    self.result_card.add_recognition_result(text, record_id)
                    self.status_display.update_status(f"识别完成: {text[:20]}...")
                    self.action_buttons.enable_result_buttons(True)
                    self.action_buttons.row.update()
                    if self.page:
                        self.page.update()
                except Exception as e:
                    logger.error(f"[DEBUG] 识别结果UI更新失败: {e}")
            self._dispatch_ui(_ui_add_recognition)

            # 提交UI更新（供TaskMonitor等使用）
            if hasattr(self.task_manager, '_submit_ui_update'):
                self.task_manager._submit_ui_update({
                    'type': 'recognition_complete',
                    'result': task.result,
                    'timestamp': time.time()
                })

    def _on_correction_complete(self, task):
        """AI修正完成回调（新系统适配）"""
        logger.info(f"[DEBUG] 修正完成回调被调用，task_id: {getattr(task, 'task_id', 'N/A')}")
        logger.info(f"[DEBUG] 修正结果: {getattr(task, 'optimized_text', getattr(task, 'corrected_text', 'N/A'))}")

        # 兼容两种字段名：optimized_text（处理器返回）或 corrected_text（统一任务）
        corrected = getattr(task, 'corrected_text', None) or getattr(task, 'optimized_text', None)
        if corrected:
            # 智能提取修正结果，过滤掉思考内容和分析过程
            filtered_corrected = self._extract_correction_result(corrected)
            print(f"[DEBUG] AI修正完成: {filtered_corrected}")

            def _ui_add_correction():
                try:
                    record_id = getattr(task, 'record_id', None)
                    if record_id:
                        self.result_card.add_correction_result(record_id, filtered_corrected)
                        logger.info(f"[DEBUG] 修正结果已关联到记录 {record_id}")
                    else:
                        # 如果没有record_id，尝试更新最近的一条记录
                        success = self.result_card.update_latest_correction(filtered_corrected)
                        if not success:
                            self.result_card.add_result(f"[修正] {filtered_corrected}", ft.Colors.ORANGE_700)
                        logger.info(f"[DEBUG] 修正结果已更新到最近记录")
                    self.status_display.update_status(f"AI修正完成: {filtered_corrected[:20]}...")
                    if self.page:
                        self.page.update()
                except Exception as e:
                    logger.error(f"[DEBUG] 添加修正结果到界面失败: {e}")
            self._dispatch_ui(_ui_add_correction)

        # 注释：新的统一任务系统会自动处理翻译流程
        # 无需手动提交翻译任务

    def _on_translation_complete(self, task):
        """翻译完成回调（新系统适配）"""
        logger.info(f"[DEBUG] 翻译完成回调被调用，task_id: {getattr(task, 'task_id', 'N/A')}")
        logger.info(f"[DEBUG] 翻译结果: {getattr(task, 'translated_text', 'N/A')}")

        if hasattr(task, 'translated_text') and task.translated_text:
            # 智能提取翻译结果，过滤掉对话过程和思考内容
            filtered_translation = self._extract_translation_result(task.translated_text)
            print(f"[DEBUG] 翻译完成: {filtered_translation}")

            def _ui_add_translation():
                try:
                    record_id = getattr(task, 'record_id', None)
                    if record_id:
                        self.result_card.add_translation_result(
                            record_id,
                            filtered_translation,
                            getattr(task, 'target_language', None)
                        )
                        logger.info(f"[DEBUG] 翻译结果已关联到记录 {record_id}")
                    else:
                        # 如果没有record_id，添加到最近的一条记录
                        success = self.result_card.update_latest_translation(filtered_translation)
                        if not success:
                            self.result_card.add_result(f"[翻译] {filtered_translation}", ft.Colors.GREEN_700)
                        logger.info(f"[DEBUG] 翻译结果已更新到最近记录")
                    self.status_display.update_status(f"翻译完成: {filtered_translation[:20]}...")
                    if self.page:
                        self.page.update()
                except Exception as e:
                    logger.error(f"[DEBUG] 添加翻译结果到界面失败: {e}")
            self._dispatch_ui(_ui_add_translation)

    def _on_ui_update(self, update_data: dict):
        """UI更新回调"""
        # 这个回调会传递给TaskMonitor处理
        pass

    def _on_statistics_update(self, stats):
        """统计更新回调"""
        # 这个回调会传递给TaskMonitor处理
        if hasattr(self, 'task_monitor') and self.task_monitor:
            self.task_monitor._on_statistics_update(stats)

    def _on_recorder_error(self, error: Exception):
        """录音器错误回调"""
        print(f"[ERROR] 录音器错误: {error}")
        self.update_status(f"录音错误: {error}")

        # 停止实时模式
        if self.realtime_toggle.is_realtime:
            self.realtime_toggle.set_realtime(False)
            self.toggle_realtime_mode(False)

    # 结果操作
    def copy_result(self, e=None):
        """复制结果"""
        text = self.result_card.get_result()
        if text:
            self.page.set_clipboard(text)
            self.update_status("已复制到剪贴板")

    def optimize_text(self, e=None):
        """AI优化文本"""
        if self.ai_processor:
            text = self.result_card.get_result()
            if text:
                # 获取最近3条上下文（不包括当前文本）
                all_recent = self.result_card.get_recent_results(4)  # 获取最近4条
                context_history = all_recent[:-1] if len(all_recent) > 1 else []  # 排除最后一条（当前文本）
                self.transcription_handler.optimize_text_async(text, context_history)

    def summarize_results(self, e=None):
        """AI汇总所有识别结果"""
        print("[DEBUG] summarize_results 被调用")

        if not self.ai_processor:
            print("[DEBUG] AI处理器未配置")
            self.update_status("请先在设置中配置AI服务")
            return

        # 获取所有识别文本（排除汇总报告）
        texts = self.result_card.get_all_recognition_texts()
        print(f"[DEBUG] 获取到 {len(texts)} 条识别记录")

        if not texts:
            self.update_status("没有可汇总的识别记录")
            return

        self.update_status(f"正在汇总 {len(texts)} 条识别记录...")
        print(f"[DEBUG] 开始汇总，文本: {texts[:2]}...")  # 打印前2条

        # 异步执行汇总
        import threading
        def summarize_worker():
            try:
                print("[DEBUG] 调用 AI summarize_text")
                print(f"[DEBUG] texts参数: {texts[:2] if len(texts) > 2 else texts}")
                result = self.ai_processor.summarize_text(texts)
                print(f"[DEBUG] AI返回结果: {result}")

                if not result:
                    print("[ERROR] AI返回None")
                    self.update_status("AI返回空结果")
                    return

                if result.get("success"):
                    summary_text = result.get("text", "")
                    record_count = result.get("record_count", len(texts))

                    # 过滤AI回答中的思考内容
                    filtered_summary = self._filter_ai_thinking_content(summary_text)
                    print(f"[DEBUG] 汇总结果过滤后: {filtered_summary[:100]}...")

                    # 保存到本地文件
                    from datetime import datetime
                    import os
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"AI汇总报告_{timestamp}.md"
                    filepath = os.path.join(os.getcwd(), filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(f"# AI汇总报告\n\n")
                        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(f"**记录数量**: {record_count} 条\n\n")
                        f.write("---\n\n")
                        f.write(filtered_summary)

                    # 添加到识别结果（特殊样式）
                    self.result_card.add_result(filtered_summary, is_summary=True)
                    self.result_card.card.update()

                    self.update_status(f"✓ 汇总完成，已保存到: {filename}")

                    # 按钮反馈
                    original_text = self.action_buttons.optimize_button.text
                    self.action_buttons.optimize_button.text = "✓ 已汇总"
                    self.action_buttons.optimize_button.update()

                    def restore_button():
                        import time
                        time.sleep(1.5)
                        self.action_buttons.optimize_button.text = original_text
                        if self.action_buttons.optimize_button.page:
                            self.action_buttons.optimize_button.update()
                    threading.Thread(target=restore_button, daemon=True).start()

                else:
                    error_msg = result.get("error", "汇总失败")
                    self.update_status(f"汇总失败: {error_msg}")

            except Exception as ex:
                print(f"[ERROR] 汇总异常: {ex}")
                import traceback
                print(f"[ERROR] 异常堆栈:\n{traceback.format_exc()}")
                self.update_status(f"汇总异常: {str(ex)}")

        threading.Thread(target=summarize_worker, daemon=True).start()

    def copy_result(self, e=None):
        """复制最新识别结果"""
        text = self.result_card.get_result()
        if text:
            self.page.set_clipboard(text)
            self.update_status("✓ 已复制到剪贴板")
            # 简短的按钮反馈
            original_text = self.action_buttons.copy_button.text
            self.action_buttons.copy_button.text = "✓ 已复制"
            self.action_buttons.copy_button.update()

            # 1秒后恢复按钮文本
            import threading
            def restore_button():
                import time
                time.sleep(1)
                self.action_buttons.copy_button.text = original_text
                if self.action_buttons.copy_button.page:
                    self.action_buttons.copy_button.update()
            threading.Thread(target=restore_button, daemon=True).start()

    def export_result(self, e=None):
        """导出识别结果为TXT文件"""
        results = self.result_card.get_all_results_with_timestamps()
        if not results:
            self.update_status("没有可导出的内容")
            return

        try:
            from datetime import datetime
            import os

            # 生成文件名（使用当前时间）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"识别结果_{timestamp}.txt"

            # 保存到当前目录
            filepath = os.path.join(os.getcwd(), filename)

            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("=" * 50 + "\n")
                f.write(f"语音识别结果导出\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"共 {len(results)} 条记录\n")
                f.write("=" * 50 + "\n\n")

                for i, item in enumerate(results, 1):
                    f.write(f"[{i}] {item['timestamp']}\n")
                    f.write(f"{item['text']}\n\n")

            self.update_status(f"✓ 已导出到: {filename}")

            # 按钮反馈
            original_text = self.action_buttons.export_button.text
            self.action_buttons.export_button.text = "✓ 已导出"
            self.action_buttons.export_button.update()

            import threading
            def restore_button():
                import time
                time.sleep(1)
                self.action_buttons.export_button.text = original_text
                if self.action_buttons.export_button.page:
                    self.action_buttons.export_button.update()
            threading.Thread(target=restore_button, daemon=True).start()

        except Exception as ex:
            self.update_status(f"导出失败: {str(ex)}")

    def clear_result(self, e=None):
        """清空结果"""
        self.result_card.clear_result()
        self.transcription_handler.clear_result()
        # 禁用按钮
        self.action_buttons.enable_result_buttons(False)
        self.action_buttons.row.update()

    def get_context_history(self) -> list:
        """获取识别结果的上下文历史（最近3条，不包括当前最新的）"""
        all_recent = self.result_card.get_recent_results(4)  # 获取最近4条
        return all_recent[:-1] if len(all_recent) > 1 else []  # 排除最后一条（当前文本）

    def _restore_last_audio_device(self):
        """恢复上次选择的音频设备"""
        try:
            last_device_index = self.settings.get("last_audio_device_index")
            last_device_name = self.settings.get("last_audio_device_name")

            if last_device_index is not None:
                print(f"[INFO] 尝试恢复音频设备: {last_device_name} (索引: {last_device_index})")

                # 获取当前可用设备列表
                devices = self.audio_engine.list_input_devices()

                # 验证设备是否仍然存在
                device_valid = False
                for device in devices:
                    if device.index == last_device_index:
                        # 设备索引匹配，进一步验证名称
                        if last_device_name and device.name == last_device_name:
                            device_valid = True
                            print(f"[INFO] 设备验证成功: {device.name}")
                        elif not last_device_name:
                            # 没有保存名称，只验证索引
                            device_valid = True
                            print(f"[INFO] 设备索引匹配: {device.name}")
                        break

                if device_valid:
                    # 设置设备
                    self.audio_device_selector.set_selected_device(last_device_index)
                    self.audio_device_selector.dropdown.update()

                    # 触发设备变更（但不重复保存）
                    self.audio_recorder.set_device(last_device_index)
                    self.update_device_status(last_device_index)
                    self._update_record_button_state()

                    print(f"[INFO] 已自动选择音频设备: {last_device_name}")
                else:
                    print(f"[WARN] 上次使用的设备不存在，使用默认设备")
                    # 清除无效的设备配置
                    self.settings["last_audio_device_index"] = None
                    self.settings["last_audio_device_name"] = None

        except Exception as e:
            print(f"[ERROR] 恢复音频设备失败: {e}")

    def _initialize_funasr_models(self):
        """初始化FunASR模型并显示进度"""
        import threading

        def init_worker():
            try:
                # 在状态栏显示加载提示
                self.update_status("正在加载语音识别模型...")
                self.page.update()

                # 初始化模型
                init_result = self.recognition_pipeline.direct_funasr.initialize()

                # 更新状态和设备信息
                if init_result.get("success"):
                    device_name = init_result.get("device", "unknown")
                    device_display = self._format_device_name(device_name)

                    self.update_status(init_result.get("message", "模型加载成功"))

                    # 更新设备显示
                    audio_device = self.device_status_text.value.split("|")[0].strip() if "|" in self.device_status_text.value else "音频设备: 默认设备"
                    self.device_status_text.value = f"{audio_device} | 计算设备: {device_display}"
                    self.device_status_text.update()
                else:
                    self.update_status(f"模型加载失败: {init_result.get('error', '未知错误')}")
                    self.device_status_text.value = self.device_status_text.value.replace("检测中...", "未知")
                    self.device_status_text.update()

            except Exception as e:
                self.update_status(f"模型加载异常: {str(e)}")

        # 启动加载线程
        thread = threading.Thread(target=init_worker, daemon=True)
        thread.start()

    def _format_device_name(self, device: str) -> str:
        """
        格式化设备名称为友好显示

        Args:
            device: 设备名称 (cuda:0, mps, xpu, cpu)

        Returns:
            str: 友好显示的设备名称
        """
        if device.startswith("cuda"):
            return "🚀 GPU (CUDA)"
        elif device == "mps":
            return "🍎 Apple Silicon (MPS)"
        elif device == "xpu":
            return "⚡ Intel GPU (XPU)"
        elif device == "cpu":
            return "💻 CPU"
        else:
            return device

    # 对话框
    def open_settings(self, e=None):
        """打开设置对话框"""
        dialog = create_settings_dialog(
            page=self.page,
            config_manager=self.config_manager,
            on_save=self.on_settings_changed
        )
        dialog.open()

    def open_help(self, e=None):
        """打开帮助对话框"""
        dialog = HelpDialog(page=self.page)
        dialog.show()

    def on_settings_changed(self, new_settings: dict):
        """设置变更回调"""
        self.settings = new_settings

        # 重新初始化AI处理器（使用新的配置结构）
        if new_settings.get("enable_ai_optimization", False):
            ai_config = self.config_manager.get_ai_service_config("correction")
            self.ai_processor = AIProcessor(
                api_key=ai_config.get("api_key", ""),
                base_url=ai_config.get("base_url", ""),
                model_name=ai_config.get("model_name", "")
            )
            self.transcription_handler.ai_processor = self.ai_processor
        else:
            self.ai_processor = None
            self.transcription_handler.ai_processor = None

        # 重新初始化任务管理器（继续使用统一任务系统）
        if hasattr(self, 'task_manager'):
            self.task_manager.stop()

        from core.task_adapter import create_task_manager
        funasr_recognizer = self.recognition_pipeline.direct_funasr if self.recognition_pipeline.use_direct_integration else None
        self.task_manager = create_task_manager(
            use_unified_system=False,
            funasr_recognizer=funasr_recognizer,
            config_manager=self.config_manager
        )

        # 设置回调函数
        self.task_manager.on_recognition_complete = self._on_recognition_complete
        self.task_manager.on_correction_complete = self._on_correction_complete
        self.task_manager.on_translation_complete = self._on_translation_complete
        self.task_manager.on_ui_update = self._on_ui_update
        self.task_manager.on_statistics_update = self._on_statistics_update

        self.task_manager.start()

        # 更新ContinuousAudioRecorder的TaskManager引用
        if hasattr(self, 'continuous_recorder'):
            self.continuous_recorder.task_manager = self.task_manager

        # 更新翻译按钮状态
        if hasattr(self, 'translation_switch'):
            self.translation_switch.value = new_settings.get("enable_translation", False)
            self.page.update()

        self.update_status("设置已更新")


def main():
    """主函数"""
    ft.app(target=QuQuFletApp, assets_dir="assets")


if __name__ == "__main__":
    main()
