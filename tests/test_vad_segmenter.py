#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hybrid VAD segmentation tests."""

import numpy as np
import pytest

from src.core.vad_system import VADConfig, HybridVADSegmenter

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.1  # seconds


def generate_silence(duration: float) -> np.ndarray:
    samples = int(SAMPLE_RATE * duration)
    return np.zeros(samples, dtype=np.int16)


def generate_tone(duration: float, frequency: float = 440.0, amplitude: float = 12000.0) -> np.ndarray:
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    return tone.astype(np.int16)


def make_config() -> VADConfig:
    return VADConfig.create_custom_config(
        MIN_SPEECH_DURATION=0.25,
        SILENCE_TIMEOUT=0.3,
        MAX_WINDOW_SIZE=2.0,
        ENERGY_THRESHOLD=200,
        ZCR_THRESHOLD=0.05,
        SMOOTHING_WINDOW=3,
        CONFIDENCE_THRESHOLD=0.5,
        OVERLAP_DURATION=0.1,
        MAX_BUFFER_DURATION=3.0,
    )


def feed_sequence(segmenter: HybridVADSegmenter, chunks) -> list:
    segments = []
    for chunk in chunks:
        segment, _ = segmenter.process_chunk(chunk)
        if segment:
            segments.append(segment)
    return segments


def test_segmenter_emits_segment_after_speech_and_silence():
    config = make_config()
    segmenter = HybridVADSegmenter(sample_rate=SAMPLE_RATE, config=config)

    silence = generate_silence(CHUNK_DURATION)
    voice = generate_tone(CHUNK_DURATION)

    chunks = [silence] * 3 + [voice] * 10 + [silence] * 5
    segments = feed_sequence(segmenter, chunks)

    assert len(segments) == 1, "Expected a single segment for one speech bout"
    segment = segments[0]

    assert segment.audio.size > 0
    assert segment.info['should_process'] is True
    assert segment.info['segment_duration'] >= pytest.approx(config.MIN_SPEECH_DURATION, rel=0.25)
    assert segment.info['energy'] > config.ENERGY_THRESHOLD


def test_segmenter_retains_overlap_tail():
    config = make_config()
    overlap = 0.12
    segmenter = HybridVADSegmenter(sample_rate=SAMPLE_RATE, config=config, overlap_duration=overlap)

    silence = generate_silence(CHUNK_DURATION)
    voice = generate_tone(CHUNK_DURATION)

    chunks = [voice] * 8 + [silence] * 4
    segments = feed_sequence(segmenter, chunks)

    assert segments, "Segmenter should have emitted a segment"
    tail_duration = segmenter.buffer.get_duration()
    assert tail_duration == pytest.approx(overlap, abs=0.03)


def test_segmenter_accepts_byte_chunks():
    config = make_config()
    segmenter = HybridVADSegmenter(sample_rate=SAMPLE_RATE, config=config)

    voice_chunk = generate_tone(CHUNK_DURATION)
    silence_chunk = generate_silence(CHUNK_DURATION)

    segments = feed_sequence(segmenter, [voice_chunk.tobytes()] * 12 + [silence_chunk] * 6)
    assert segments, "Processing byte chunks should still produce a segment"
