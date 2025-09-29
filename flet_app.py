#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蛐蛐 (QuQu) - Flet 原型应用
基于 Flet 的现代化语音转文字应用
"""

import os
import sys
import json
import tempfile
import threading
import time
import wave
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import flet as ft
import pyaudio
import numpy as np
from datetime import datetime

# 音频录制参数
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 30

class QuQuFletApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "蛐蛐 (QuQu) - 智能语音助手"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # 设置窗口为竖版布局
        self.page.window.width = 480
        self.page.window.height = 800
        self.page.window.min_width = 400
        self.page.window.min_height = 600
        self.page.window.resizable = True

        # 设置应用图标
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.page.window.icon = icon_path

        # 状态变量
        self.is_recording = False
        self.audio_stream = None
        self.audio_frames = []
        self.current_audio_file = None
        self.transcription_result = ""
        self.funasr_process = None

        # 配置变量
        self.settings = {
            "api_key": "",
            "base_url": "",
            "model_name": "",
            "language": "zh",
            "use_vad": True,
            "use_punc": True
        }

        # 创建UI组件
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 顶部标题栏
        self.header = ft.Column(
            [
                ft.Text(
                    "🎤 蛐蛐 (QuQu)",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700,
                ),
                ft.Text(
                    "开源免费的智能语音助手",
                    size=16,
                    color=ft.Colors.GREY_600,
                ),
                ft.Divider(height=20),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 录音控制区域
        self.record_button = ft.ElevatedButton(
            text="开始录音",
            icon=ft.Icons.MIC,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=5,
                side=ft.BorderSide(width=2, color=ft.Colors.BLUE_500),
            ),
            on_click=self.toggle_recording,
            width=200,
            height=60,
        )

        self.status_text = ft.Text(
            "准备就绪",
            size=16,
            color=ft.Colors.GREY_700,
        )

        self.recording_progress = ft.ProgressBar(
            value=0,
            width=300,
            bar_height=8,
            color=ft.Colors.BLUE_500,
            bgcolor=ft.Colors.BLUE_100,
        )

        # 录音控制区域
        self.recording_section = ft.Column(
            [
                self.record_button,
                ft.Container(height=10),
                self.status_text,
                ft.Container(height=10),
                self.recording_progress,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 结果显示区域
        self.result_text = ft.Text(
            "点击录音按钮开始...",
            size=14,
            color=ft.Colors.GREY_600,
            selectable=True,
        )

        self.result_card = ft.Card(
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.TEXT_FORMAT, color=ft.Colors.BLUE_500),
                                ft.Text(
                                    "识别结果",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Divider(height=10),
                        self.result_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
            ),
            elevation=3,
            width=440,  # 调整为适合竖版布局的宽度
        )

        # 操作按钮区域
        self.action_buttons = ft.Row(
            [
                ft.ElevatedButton(
                    text="复制文本",
                    icon=ft.Icons.COPY,
                    on_click=self.copy_text,
                    disabled=True,
                ),
                ft.ElevatedButton(
                    text="清空结果",
                    icon=ft.Icons.CLEAR,
                    on_click=self.clear_result,
                    disabled=True,
                ),
                ft.ElevatedButton(
                    text="设置",
                    icon=ft.Icons.SETTINGS,
                    on_click=self.open_settings,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # 状态信息区域
        self.status_info = ft.Text(
            "系统就绪，准备录音",
            size=14,
            color=ft.Colors.GREY_600,
        )

        self.status_section = ft.Container(
            padding=20,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_500),
                            ft.Text(
                                "状态信息",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Divider(height=5),
                    self.status_info,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )

        # 添加所有组件到页面
        self.page.add(
            ft.Column(
                [
                    self.header,
                    self.recording_section,
                    ft.Container(height=20),
                    self.result_card,
                    ft.Container(height=20),
                    self.action_buttons,
                    ft.Container(height=20),
                    self.status_section,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        # 加载配置
        self.load_settings_from_file()

        # 初始化音频系统
        self.init_audio_system()

    def init_audio_system(self):
        """初始化音频系统"""
        try:
            self.audio = pyaudio.PyAudio()
            self.update_status("音频系统初始化成功")
        except Exception as e:
            self.update_status(f"音频系统初始化失败: {str(e)}")
            self.record_button.disabled = True
            self.page.update()

    def toggle_recording(self, e):
        """切换录音状态"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始录音"""
        try:
            self.is_recording = True
            self.audio_frames = []

            # 更新UI
            self.record_button.text = "停止录音"
            self.record_button.icon = ft.Icons.STOP
            self.record_button.style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=5,
                side=ft.BorderSide(width=2, color=ft.Colors.RED_500),
                bgcolor=ft.Colors.RED_500,
            )
            self.status_text.value = "正在录音..."
            self.status_text.color = ft.Colors.RED_700
            self.recording_progress.value = 0

            # 开始音频流
            self.audio_stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=self.audio_callback
            )

            # 启动进度更新线程
            self.start_progress_timer()

            self.update_status("录音开始")
            self.page.update()

        except Exception as e:
            self.update_status(f"开始录音失败: {str(e)}")
            self.is_recording = False
            self.page.update()

    def stop_recording(self):
        """停止录音"""
        try:
            self.is_recording = False

            # 停止音频流
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None

            # 更新UI
            self.record_button.text = "开始录音"
            self.record_button.icon = ft.Icons.MIC
            self.record_button.style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=5,
                side=ft.BorderSide(width=2, color=ft.Colors.BLUE_500),
            )
            self.status_text.value = "处理中..."
            self.status_text.color = ft.Colors.ORANGE_700

            # 保存音频文件
            self.save_audio_file()

            self.update_status("录音停止，正在处理...")
            self.page.update()

            # 启动转录处理
            self.process_transcription()

        except Exception as e:
            self.update_status(f"停止录音失败: {str(e)}")
            self.page.update()

    def audio_callback(self, in_data, frame_count, time_info, status):
        """音频录制回调"""
        if self.is_recording:
            self.audio_frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def start_progress_timer(self):
        """启动进度计时器 - 使用 Flet 0.28.3 推荐的线程方法"""
        def update_progress():
            """在后台线程中更新录音进度"""
            start_time = time.time()
            while self.is_recording:
                elapsed = time.time() - start_time
                progress = min(elapsed / RECORD_SECONDS, 1.0)

                # 更新进度条 - Flet 0.28.3 中在 run_thread 内可以直接调用 update
                self.recording_progress.value = progress
                self.page.update()

                # 如果达到最大录音时间，自动停止
                if elapsed >= RECORD_SECONDS:
                    # 直接调用停止录音 - Flet 会处理线程安全
                    self.stop_recording()
                    break

                time.sleep(0.1)

        # 使用 Flet 0.28.3 官方线程方法启动进度更新
        self.page.run_thread(update_progress)

    def save_audio_file(self):
        """保存音频文件"""
        try:
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_audio_file = os.path.join(temp_dir, f"ququ_recording_{timestamp}.wav")

            # 保存为WAV文件
            with wave.open(self.current_audio_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.audio_frames))

            self.update_status(f"音频文件已保存: {self.current_audio_file}")

        except Exception as e:
            self.update_status(f"保存音频文件失败: {str(e)}")

    def process_transcription(self):
        """处理转录 - 使用 Flet 0.28.3 推荐的线程安全方法"""
        if not self.current_audio_file:
            self.update_status("没有可处理的音频文件")
            return

        # 使用 Flet 官方推荐的 page.run_thread() 方法启动后台任务
        # 这是 Flet 0.28.3 版本的正确线程安全实现方式
        def transcribe_in_background():
            """在后台线程中执行转录任务"""
            try:
                # 使用FunASR服务器进行转录
                result = self.transcribe_with_funasr(self.current_audio_file)

                # 更新转录结果 - 在后台线程中直接调用，Flet会处理线程安全
                self.update_transcription_result(result)

            except Exception as e:
                error_msg = f"转录失败: {str(e)}"
                # 更新错误状态 - 在后台线程中直接调用，Flet会处理线程安全
                self.update_status(error_msg)

        # 使用 Flet 0.28.3 的官方线程方法 - 自动处理线程安全
        self.page.run_thread(transcribe_in_background)

    def transcribe_with_funasr(self, audio_file: str) -> Dict[str, Any]:
        """使用FunASR进行转录 - 修复版本"""
        try:
            # 检查FunASR服务器脚本
            funasr_script = os.path.join(os.path.dirname(__file__), "funasr_server.py")

            if not os.path.exists(funasr_script):
                return {
                    "success": False,
                    "error": "FunASR服务器脚本不存在",
                    "text": "FunASR服务器脚本不存在"
                }

            # 准备命令输入 - 修复 JSON 换行符问题
            input_data = {
                "action": "transcribe",
                "audio_path": audio_file,
                "options": {
                    "use_vad": True,
                    "use_punc": True,
                    "language": "zh"
                }
            }

            # 修复：使用正确的输入格式，添加换行符让服务器知道命令结束
            input_text = json.dumps(input_data, ensure_ascii=False) + '\n'

            # 运行FunASR服务器进行转录 - 修复超时和缓冲问题
            process = subprocess.Popen(
                [sys.executable, funasr_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0  # 无缓冲模式
            )

            try:
                # 发送命令并获取响应 - 增加超时时间
                stdout, stderr = process.communicate(input=input_text, timeout=120)

                if process.returncode == 0:
                    # 解析第一行的初始化结果，第二行的转录结果
                    lines = stdout.strip().split('\n')
                    if len(lines) >= 2:
                        # 尝试解析转录结果（通常是最后一行）
                        try:
                            result_line = lines[-1]
                            output = json.loads(result_line)

                            if output.get("success"):
                                return {
                                    "success": True,
                                    "text": output.get("text", ""),
                                    "confidence": output.get("confidence", 0.0),
                                    "duration": output.get("duration", 0.0)
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": output.get("error", "转录失败"),
                                    "text": f"转录失败: {output.get('error', '未知错误')}"
                                }
                        except json.JSONDecodeError as je:
                            return {
                                "success": False,
                                "error": f"解析转录结果失败: {str(je)}",
                                "text": f"解析失败，原始输出: {stdout[:200]}..."
                            }
                    else:
                        return {
                            "success": False,
                            "error": "服务器响应格式错误",
                            "text": f"响应行数不足: {len(lines)}, 内容: {stdout[:200]}..."
                        }
                else:
                    return {
                        "success": False,
                        "error": f"服务器执行失败 (代码: {process.returncode})",
                        "text": f"错误信息: {stderr[:200]}..."
                    }

            finally:
                # 确保进程被正确关闭
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "转录超时",
                "text": "转录超时，请稍后重试"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": f"转录异常: {str(e)}"
            }

    def update_transcription_result(self, result: Dict[str, Any]):
        """更新转录结果"""
        if result.get("success"):
            self.transcription_result = result.get("text", "")
            self.result_text.value = self.transcription_result
            self.status_text.value = "转录完成"
            self.status_text.color = ft.Colors.GREEN_700

            # 启用操作按钮
            self.action_buttons.controls[0].disabled = False  # 复制按钮
            self.action_buttons.controls[1].disabled = False  # 清空按钮

            # 显示置信度
            confidence = result.get("confidence", 0.0)
            duration = result.get("duration", 0.0)
            self.update_status(f"转录成功 - 置信度: {confidence:.2f}, 时长: {duration:.2f}秒")
        else:
            self.result_text.value = result.get("text", "转录失败")
            self.status_text.value = "转录失败"
            self.status_text.color = ft.Colors.RED_700
            self.update_status(f"转录失败: {result.get('error', '未知错误')}")

        self.page.update()

    def copy_text(self, e):
        """复制文本到剪贴板"""
        if self.transcription_result:
            self.page.set_clipboard(self.transcription_result)
            self.update_status("文本已复制到剪贴板")
            self.page.update()

    def clear_result(self, e):
        """清空结果"""
        self.transcription_result = ""
        self.result_text.value = "点击录音按钮开始..."
        self.status_text.value = "准备就绪"
        self.status_text.color = ft.Colors.GREY_700

        # 禁用操作按钮
        self.action_buttons.controls[0].disabled = True
        self.action_buttons.controls[1].disabled = True

        self.update_status("结果已清空")
        self.page.update()

    def update_status(self, message: str):
        """更新状态信息"""
        self.status_info.value = f"{datetime.now().strftime('%H:%M:%S')} - {message}"
        self.page.update()

    def open_settings(self, e):
        """打开设置对话框"""
        # 创建配置输入字段
        api_key_field = ft.TextField(
            label="API Key",
            value=self.settings["api_key"],
            password=True,
            can_reveal_password=True,
            width=400,
        )

        base_url_field = ft.TextField(
            label="Base URL",
            value=self.settings["base_url"],
            width=400,
            hint_text="例如: https://api.openai.com/v1",
        )

        model_name_field = ft.TextField(
            label="模型名称",
            value=self.settings["model_name"],
            width=400,
            hint_text="例如: gpt-3.5-turbo, qwen-turbo",
        )

        language_field = ft.Dropdown(
            label="语言",
            value=self.settings["language"],
            width=200,
            options=[
                ft.dropdown.Option("zh", "中文"),
                ft.dropdown.Option("en", "英文"),
            ],
        )

        use_vad_field = ft.Checkbox(
            label="使用语音活动检测(VAD)",
            value=self.settings["use_vad"],
        )

        use_punc_field = ft.Checkbox(
            label="使用标点符号恢复",
            value=self.settings["use_punc"],
        )

        def save_settings(e):
            self.settings["api_key"] = api_key_field.value
            self.settings["base_url"] = base_url_field.value
            self.settings["model_name"] = model_name_field.value
            self.settings["language"] = language_field.value
            self.settings["use_vad"] = use_vad_field.value
            self.settings["use_punc"] = use_punc_field.value

            # 保存配置到文件
            self.save_settings_to_file()

            self.page.close(dlg)
            self.update_status("设置已保存")

        def test_connection(e):
            # 这里可以添加测试连接的功能
            self.update_status("测试连接功能待实现")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("应用设置"),
            content=ft.Column(
                [
                    ft.Text("AI服务配置", size=18, weight=ft.FontWeight.BOLD),
                    api_key_field,
                    base_url_field,
                    model_name_field,
                    ft.Divider(height=20),
                    ft.Text("语音识别设置", size=18, weight=ft.FontWeight.BOLD),
                    language_field,
                    use_vad_field,
                    use_punc_field,
                ],
                width=450,
                height=400,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            actions=[
                ft.TextButton("测试连接", on_click=test_connection),
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("保存", on_click=save_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dlg)

    def save_settings_to_file(self):
        """保存配置到文件"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), "ququ_settings.json")
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")

    def load_settings_from_file(self):
        """从文件加载配置"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), "ququ_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
        except Exception as e:
            print(f"加载设置失败: {e}")

    def on_window_close(self, e):
        """窗口关闭事件处理"""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()

            if hasattr(self, 'audio'):
                self.audio.terminate()

            # 清理临时文件
            if self.current_audio_file and os.path.exists(self.current_audio_file):
                os.remove(self.current_audio_file)

        except Exception as e:
            print(f"清理资源时发生错误: {e}")

def main():
    """主函数"""
    # 设置Flet应用
    ft.app(target=QuQuFletApp, assets_dir="assets")

if __name__ == "__main__":
    main()