"""Open Transcribe — CPU-optimized streaming speech-to-text with terminal UI."""

__version__ = "0.1.0"
__author__ = "Open Transcribe Contributors"

from src.config import Config
from src.audio_stream import AudioStream

__all__ = ["Config", "AudioStream", "__version__"]
