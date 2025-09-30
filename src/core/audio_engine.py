#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audio engine abstraction for QuQu.

Provides a thin wrapper around PyAudio/PyAudioWPatch so UI code can focus on
workflow orchestration while this module handles backend selection, device
enumeration, and stream lifecycle management."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

try:  # Prefer WASAPI-enabled backend when available.
    import pyaudiowpatch as _pyaudio
    AUDIO_BACKEND_NAME = "PyAudioWPatch"
except ImportError:  # Fall back to vanilla PyAudio if needed.
    try:
        import pyaudio as _pyaudio  # type: ignore
        AUDIO_BACKEND_NAME = "PyAudio"
    except ImportError:  # PyAudio unavailable; callers must guard against this.
        _pyaudio = None  # type: ignore
        AUDIO_BACKEND_NAME = "None"


@dataclass
class AudioDeviceInfo:
    """Simplified descriptor for an input device."""

    index: int
    name: str
    max_input_channels: int
    host_api: str
    is_default: bool = False
    is_wasapi: bool = False
    is_loopback: bool = False


@dataclass
class AudioStreamConfig:
    """Configuration for opening an input stream."""

    format: int
    channels: int
    rate: int
    chunk: int
    device_index: Optional[int] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AudioStreamConfig":
        return cls(
            format=payload["format"],
            channels=payload["channels"],
            rate=payload["rate"],
            chunk=payload["chunk"],
            device_index=payload.get("device_index"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "channels": self.channels,
            "rate": self.rate,
            "chunk": self.chunk,
            "device_index": self.device_index,
        }


@dataclass
class AudioTestResult:
    """Outcome of a quick stream probe."""

    success: bool
    message: str
    backend: str = AUDIO_BACKEND_NAME
    config: Optional[AudioStreamConfig] = None


class AudioEngine:
    """Encapsulates audio device discovery and stream lifecycle."""

    def __init__(
        self,
        sample_rate: int = 16_000,
        chunk_size: int = 1_024,
        channels: int = 1,
        audio_format: Optional[int] = None,
    ) -> None:
        if _pyaudio is None:
            raise RuntimeError("PyAudio backend is not available on this system.")

        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.audio_format = audio_format if audio_format is not None else _pyaudio.paInt16
        self._pa: Optional[_pyaudio.PyAudio] = None

    @property
    def backend_name(self) -> str:
        return AUDIO_BACKEND_NAME

    @property
    def interface(self) -> _pyaudio.PyAudio:
        if self._pa is None:
            raise RuntimeError("AudioEngine has not been initialised. Call initialise().")
        return self._pa

    def initialise(self) -> None:
        if self._pa is None:
            self._pa = _pyaudio.PyAudio()

    def terminate(self) -> None:
        if self._pa is not None:
            self._pa.terminate()
            self._pa = None

    # ------------------------------------------------------------------
    # Compatibility helpers for legacy call sites
    # ------------------------------------------------------------------
    def get_device_count(self) -> int:
        return self.interface.get_device_count()

    def get_default_input_device_info(self) -> Dict[str, Any]:
        return self.interface.get_default_input_device_info()

    def get_device_info_by_index(self, index: int) -> Dict[str, Any]:
        return self.interface.get_device_info_by_index(index)

    # ------------------------------------------------------------------
    # Device enumeration helpers
    # ------------------------------------------------------------------
    def list_input_devices(self) -> List[AudioDeviceInfo]:
        devices: List[AudioDeviceInfo] = []
        default_index = self._safe_default_input_index()

        for index in range(self.interface.get_device_count()):
            info = self.interface.get_device_info_by_index(index)
            if info.get("maxInputChannels", 0) <= 0:
                continue

            name = info.get("name", f"Device #{index}")
            host_api_name = self._host_api_name(info.get("hostApi"))
            is_wasapi = "WASAPI" in host_api_name or "WASAPI" in name
            is_loopback = "loopback" in name.lower() or "stereo mix" in name.lower()

            devices.append(
                AudioDeviceInfo(
                    index=index,
                    name=name,
                    max_input_channels=info.get("maxInputChannels", 0),
                    host_api=host_api_name,
                    is_default=index == default_index,
                    is_wasapi=is_wasapi,
                    is_loopback=is_loopback,
                )
            )

        return devices

    def _safe_default_input_index(self) -> Optional[int]:
        with contextlib.suppress(Exception):
            info = self.interface.get_default_input_device_info()
            return info.get("index")
        return None

    def _host_api_name(self, host_api_index: Optional[int]) -> str:
        if host_api_index is None:
            return "Unknown"
        with contextlib.suppress(Exception):
            api_info = self.interface.get_host_api_info_by_index(host_api_index)
            return api_info.get("name", "Unknown")
        return "Unknown"

    # ------------------------------------------------------------------
    # Stream management helpers
    # ------------------------------------------------------------------
    def open_input_stream(
        self,
        config: Optional[AudioStreamConfig] = None,
        *,
        start: bool = True,
        **overrides: Any,
    ):
        cfg = config or AudioStreamConfig(
            format=self.audio_format,
            channels=self.channels,
            rate=self.sample_rate,
            chunk=self.chunk_size,
        )
        params = cfg.to_dict()
        params.update(overrides)

        stream = self.interface.open(
            format=params["format"],
            channels=params["channels"],
            rate=params["rate"],
            input=True,
            frames_per_buffer=params["chunk"],
            input_device_index=params.get("device_index"),
            start=start,
        )
        return stream

    # Legacy alias used by existing UI code.
    def open(self, **kwargs):
        cfg = AudioStreamConfig(
            format=kwargs.get("format", self.audio_format),
            channels=kwargs.get("channels", self.channels),
            rate=kwargs.get("rate", self.sample_rate),
            chunk=kwargs.get("frames_per_buffer", self.chunk_size),
            device_index=kwargs.get("input_device_index"),
        )
        return self.open_input_stream(cfg, start=kwargs.get("start", True))

    def close_stream(self, stream) -> None:
        with contextlib.suppress(Exception):
            stream.stop_stream()
        with contextlib.suppress(Exception):
            stream.close()

    def get_sample_size(self, audio_format: Optional[int] = None) -> int:
        return self.interface.get_sample_size(audio_format or self.audio_format)

    # ------------------------------------------------------------------
    # Quick probe helpers used during capability tests
    # ------------------------------------------------------------------
    def probe_stream(
        self,
        configs: Iterable[AudioStreamConfig],
        *,
        read_cycles: int = 5,
    ) -> AudioTestResult:
        for cfg in configs:
            try:
                stream = self.open_input_stream(cfg, start=True)
                try:
                    for _ in range(read_cycles):
                        stream.read(cfg.chunk, exception_on_overflow=False)
                finally:
                    self.close_stream(stream)
                return AudioTestResult(True, "stream probe succeeded", config=cfg)
            except Exception as exc:  # Try next configuration on failure.
                last_error = exc
                continue
        message = f"all stream probes failed: {last_error}" if 'last_error' in locals() else "probe failed"
        return AudioTestResult(False, message)


__all__ = [
    "AUDIO_BACKEND_NAME",
    "AudioDeviceInfo",
    "AudioEngine",
    "AudioStreamConfig",
    "AudioTestResult",
]
