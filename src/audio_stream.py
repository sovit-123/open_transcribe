"""Audio streaming engine using RealtimeSTT.

Only parameters that RealtimeSTT actually accepts are used.
"""

from typing import Optional, Callable
from RealtimeSTT import AudioToTextRecorder
import threading

from src.config import Config


class AudioStream:
    """Real-time audio capture => transcription via RealtimeSTT.

    Provides two callback streams:
        on_realtime:  partial text while you are still speaking (streaming)
        on_final:     final confident text after you pause speaking
    """

    def __init__(
        self,
        config: Config,
        on_realtime: Optional[Callable[[str], None]] = None,
        on_final: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.config = config
        self.on_realtime = on_realtime
        self.on_final = on_final
        self.on_error = on_error
        self.recorder: Optional[AudioToTextRecorder] = None
        self.is_listening = False
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Create the AudioToTextRecorder.  Heavy (downloads model on first run)."""
        self.recorder = AudioToTextRecorder(
            model=self.config.model,
            language=self.config.language,
            device=self.config.device,
            compute_type=self.config.compute_type,
            spinner=False,
            enable_realtime_transcription=self.config.enable_realtime_transcription,
            on_realtime_transcription_update=self._handle_realtime,
            post_speech_silence_duration=self.config.post_speech_silence_duration,
            silero_deactivity_detection=True,
            # min_gap_between_recordings=self.config.min_gap_between_recordings,
            # min_length_of_recording=self.config.min_length_of_recording,
        )

    def start(self) -> None:
        """Begin capturing audio in a background thread."""
        if self.is_listening:
            return
        if self.recorder is None:
            self.initialize()

        self.is_listening = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop capturing (but don't destroy the recorder so we can resume)."""
        self.is_listening = False

    def shutdown(self) -> None:
        """Fully destroy the recorder."""
        self.is_listening = False
        if self.recorder:
            try:
                self.recorder.shutdown()
            except Exception:
                pass
            self.recorder = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _handle_realtime(self, text: str) -> None:
        if text and self.on_realtime:
            self.on_realtime(text)

    def _handle_final(self, text: str) -> None:
        if text and self.on_final:
            cleaned_text = text.strip()
            if cleaned_text:
                self.on_final(cleaned_text)

    def _loop(self) -> None:
        if not self.recorder:
            return
        try:
            while self.is_listening:
                try:
                    if self.on_final:
                        self.recorder.text(self._handle_final)
                    else:
                        text = self.recorder.text()
                        if text and text.strip():
                            self._handle_final(text)
                except Exception as exc:
                    if self.on_error:
                        self.on_error(str(exc))
                    if not self.is_listening:
                        break
        except KeyboardInterrupt:
            pass
        finally:
            self.is_listening = False
