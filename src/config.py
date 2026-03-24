"""Configuration management for Open Transcribe."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Config:
    """Configuration for Open Transcribe speech-to-text.

    All defaults are battle-tested on Windows/Mac/Linux CPU.
    """

    # Model
    # (tiny, tiny.en, base, base.en, 
    # small, small.en, distil-small.en, medium, medium.en, \
    # distil-medium.en, large-v1,
    # large-v2, large-v3, large, distil-large-v2, 
    # distil-large-v3, large-v3-turbo, or turbo)
    model: str = "base"
    language: str = "en"
    device: Literal["cpu", "cuda"] = "cuda"
    compute_type: str = "float32"

    # Realtime STT behaviour
    enable_realtime_transcription: bool = True
    post_speech_silence_duration: float = 1.0  # seconds of silence before finalizing

    # UI
    app_title: str = "Open Transcribe"

    def summary(self) -> str:
        return f"model={self.model}  device={self.device}  compute={self.compute_type}"