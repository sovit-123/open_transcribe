"""Open Transcribe — a gorgeous real-time speech-to-text TUI.

Two-panel design:
  • Top: live streaming partial text (grey, updating as you speak)
  • Bottom: finalized transcript log (green, locked-in sentences)

Key bindings:
  r / Space  — toggle listening on/off
  c          — clear transcript
  q          — quit
"""

from __future__ import annotations

import time
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static, RichLog
from textual import work
from rich.text import Text

from src.config import Config
from src.audio_stream import AudioStream


# ── Widgets ──────────────────────────────────────────────────────────────

class MicIndicator(Static):
    """Pulsing microphone status bar."""

    state = reactive("idle")  # idle | loading | listening | paused | error

    _STYLES = {
        "idle":      ("○", "dim white",  "Waiting to initialize…"),
        "loading":   ("◌", "yellow",     "Loading model — hang tight…"),
        "listening": ("●", "bold green",  "LISTENING — speak now"),
        "paused":    ("■", "bold red",    "PAUSED — press [bold]R[/bold] to resume"),
        "error":     ("✗", "bold red",    "ERROR"),
    }

    def render(self) -> Text:
        icon, style, label = self._STYLES.get(self.state, self._STYLES["idle"])
        return Text.from_markup(f"  [{style}]{icon}[/{style}]  {label}")


class StreamingLine(Static):
    """Shows the partial / in-progress transcription (like watching an LLM type)."""

    partial = reactive("")

    def render(self) -> Text:
        if not self.partial:
            return Text.from_markup(
                "[dim italic]Start speaking and words will appear here in real-time…[/dim italic]"
            )
        return Text.from_markup(f"[bold bright_white]{self.partial}[/bold bright_white]▌")


# ── Main App ─────────────────────────────────────────────────────────────

class TranscribeApp(App):
    """Open Transcribe TUI — real-time streaming speech-to-text."""

    TITLE = "Open Transcribe"
    SUB_TITLE = "Real-time Speech to Text"

    BINDINGS = [
        Binding("r", "toggle_listening", "Record (R)", show=True),
        Binding("space", "toggle_listening", "Record", show=False),
        Binding("c", "clear_transcript", "Clear (C)", show=True),
        Binding("q", "quit_app", "Quit (Q)", show=True),
    ]

    CSS = """
    Screen {
        background: #0e0e12;
    }

    #mic {
        dock: top;
        height: 3;
        background: #16161e;
        border-bottom: solid #2a2a3d;
        padding: 0 1;
    }

    #streaming_box {
        height: 5;
        background: #1a1a26;
        border: round #3a3a5c;
        padding: 1 2;
        margin: 1 2 0 2;
    }

    #transcript_log {
        background: #12121a;
        border: round #2a2a3d;
        padding: 1 2;
        margin: 0 2 1 2;
    }

    Footer {
        background: #16161e;
    }

    Header {
        background: #16161e;
        color: #7aa2f7;
    }
    """

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.audio: AudioStream | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield MicIndicator(id="mic")
        with Vertical():
            yield StreamingLine(id="streaming_box")
            yield RichLog(id="transcript_log", highlight=True, markup=True, wrap=True)
        yield Footer()

    # ── Lifecycle ─────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self.sub_title = self.config.summary()

        mic = self.query_one("#mic", MicIndicator)
        mic.state = "loading"

        log = self.query_one("#transcript_log", RichLog)
        log.write(Text.from_markup("[dim]Welcome to Open Transcribe.  Press [bold]R[/bold] to start recording.[/dim]"))
        log.write("")

        self.audio = AudioStream(
            config=self.config,
            on_realtime=self._on_realtime,
            on_final=self._on_final,
            on_error=self._on_error,
        )

        self._load_model()

    @work(thread=True)
    def _load_model(self) -> None:
        try:
            self.audio.initialize()
            self.call_from_thread(self._model_ready)
        except Exception as exc:
            self.call_from_thread(self._model_failed, str(exc))

    def _model_ready(self) -> None:
        mic = self.query_one("#mic", MicIndicator)
        mic.state = "idle"
        log = self.query_one("#transcript_log", RichLog)
        log.write(Text.from_markup("[green]✓ Model loaded.  Press [bold]R[/bold] to begin.[/green]"))
        log.write("")

    def _model_failed(self, err: str) -> None:
        mic = self.query_one("#mic", MicIndicator)
        mic.state = "error"
        log = self.query_one("#transcript_log", RichLog)
        log.write(Text.from_markup(f"[bold red]✗ Failed to load model:[/bold red] {err}"))

    # ── Actions ───────────────────────────────────────────────────────

    def action_toggle_listening(self) -> None:
        if self.audio is None or self.audio.recorder is None:
            return

        mic = self.query_one("#mic", MicIndicator)

        if self.audio.is_listening:
            self.audio.stop()
            mic.state = "paused"
        else:
            self.audio.start()
            mic.state = "listening"
            self._start_time = time.time()

    def action_clear_transcript(self) -> None:
        log = self.query_one("#transcript_log", RichLog)
        log.clear()
        stream = self.query_one("#streaming_box", StreamingLine)
        stream.partial = ""
        log.write(Text.from_markup("[dim]Transcript cleared.[/dim]"))
        log.write("")

    def action_quit_app(self) -> None:
        if self.audio:
            self.audio.shutdown()
        self.exit()

    # ── Callbacks (called from audio thread) ──────────────────────────

    def _on_realtime(self, text: str) -> None:
        """Streaming partial — update the top line like an LLM typing."""
        self.call_from_thread(self._set_partial, text)

    def _on_final(self, text: str) -> None:
        """Final sentence — lock it in to the transcript log."""
        self.call_from_thread(self._append_final, text)

    def _on_error(self, err: str) -> None:
        self.call_from_thread(self._show_error, err)

    # ── Thread-safe UI updates ────────────────────────────────────────

    def _set_partial(self, text: str) -> None:
        stream = self.query_one("#streaming_box", StreamingLine)
        stream.partial = text

    def _append_final(self, text: str) -> None:
        # Clear the streaming line
        stream = self.query_one("#streaming_box", StreamingLine)
        stream.partial = ""

        # Add to the permanent log with timestamp
        ts = datetime.now().strftime("%H:%M:%S")
        log = self.query_one("#transcript_log", RichLog)
        log.write(Text.from_markup(f"[dim]{ts}[/dim]  [bold bright_green]{text}[/bold bright_green]"))

    def _show_error(self, err: str) -> None:
        log = self.query_one("#transcript_log", RichLog)
        log.write(Text.from_markup(f"[bold red]⚠  {err}[/bold red]"))

