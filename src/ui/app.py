"""Open Transcribe - a gorgeous real-time speech-to-text TUI.

Two-panel design:
  • Top: live streaming partial text (grey, updating as you speak)
  • Bottom: finalized transcript log (green, locked-in sentences)

Key bindings:
  r / Space  - toggle listening on/off
  c          - clear transcript
  q          - quit
"""

from __future__ import annotations

import time
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, RichLog, Select, Static
from textual import work
from rich.text import Text

from src.config import Config
from src.audio_stream import AudioStream


SAFE_MODELS = [
    "tiny",
    "tiny.en",
    "base",
    "base.en",
    "small",
    "small.en",
    "medium",
    "medium.en",
    "large-v3",
    "large-v3-turbo",
]


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

    #body {
        height: 1fr;
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

    #controls {
        height: 7;
        background: #12121a;
        border: round #2a2a3d;
        padding: 1 1;
        margin: 1 2 0 2;
        align: left middle;
    }

    .control_label {
        width: auto;
        content-align: left middle;
        color: #7aa2f7;
        margin-right: 1;
    }

    #model_select {
        width: 24;
        margin-right: 2;
    }

    #device_select {
        width: 18;
        margin-right: 2;
    }

    #load_model_btn {
        width: 16;
        content-align: center middle;
    }

    Select {
        color: #e5e9f0;
    }

    Button {
        color: #e5e9f0;
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
        self.model_loaded = False
        self.is_loading = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield MicIndicator(id="mic")
        with Vertical(id="body"):
            with Horizontal(id="controls"):
                yield Static("Model", classes="control_label")
                yield Select(
                    options=[(model, model) for model in SAFE_MODELS],
                    value=self.config.model if self.config.model in SAFE_MODELS else "base",
                    allow_blank=False,
                    id="model_select",
                )
                yield Static("Device", classes="control_label")
                yield Select(
                    options=[("CPU", "cpu"), ("GPU (CUDA)", "cuda")],
                    value=self.config.device,
                    allow_blank=False,
                    id="device_select",
                )
                yield Button("Load Model", id="load_model_btn")
            yield StreamingLine(id="streaming_box")
            yield RichLog(id="transcript_log", highlight=True, markup=True, wrap=True)
        yield Footer()

    # ── Lifecycle ─────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self.sub_title = self.config.summary()

        mic = self.query_one("#mic", MicIndicator)
        mic.state = "idle"

        log = self.query_one("#transcript_log", RichLog)
        log.write(Text.from_markup("[dim]Welcome to Open Transcribe.[/dim]"))
        log.write(Text.from_markup("[dim]Choose model/device, then press [bold]Load Model[/bold].[/dim]"))
        log.write("")

        self.audio = AudioStream(
            config=self.config,
            on_realtime=self._on_realtime,
            on_final=self._on_final,
            on_error=self._on_error,
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "load_model_btn":
            self._start_model_load()

    def on_select_changed(self, event: Select.Changed) -> None:
        model_select = self.query_one("#model_select", Select)
        device_select = self.query_one("#device_select", Select)

        if model_select.is_blank() or device_select.is_blank():
            return

        selected_model = str(model_select.value)
        selected_device = str(device_select.value)

        if selected_model in SAFE_MODELS and selected_device in {"cpu", "cuda"}:
            self.sub_title = (
                f"model={selected_model}  device={selected_device}  compute={self.config.compute_type}"
            )

    def _start_model_load(self) -> None:
        if self.is_loading:
            return

        model_select = self.query_one("#model_select", Select)
        device_select = self.query_one("#device_select", Select)

        if model_select.is_blank() or device_select.is_blank():
            log = self.query_one("#transcript_log", RichLog)
            log.write(Text.from_markup("[bold red]Select both model and device before loading.[/bold red]"))
            return

        model = str(model_select.value)
        device = str(device_select.value)

        if model not in SAFE_MODELS or device not in {"cpu", "cuda"}:
            log = self.query_one("#transcript_log", RichLog)
            log.write(Text.from_markup("[bold red]Invalid model or device selection.[/bold red]"))
            return

        self.config.model = model
        self.config.device = device
        self.sub_title = self.config.summary()

        if self.audio is None:
            self.audio = AudioStream(
                config=self.config,
                on_realtime=self._on_realtime,
                on_final=self._on_final,
                on_error=self._on_error,
            )
        else:
            self.audio.shutdown()

        mic = self.query_one("#mic", MicIndicator)
        mic.state = "loading"
        self.is_loading = True
        self.model_loaded = False
        self._set_controls_enabled(False)

        log = self.query_one("#transcript_log", RichLog)
        log.write(Text.from_markup(
            f"[dim]Loading model [bold]{self.config.model}[/bold] on [bold]{self.config.device}[/bold]...[/dim]"
        ))

        self._load_model()

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.query_one("#model_select", Select).disabled = not enabled
        self.query_one("#device_select", Select).disabled = not enabled
        self.query_one("#load_model_btn", Button).disabled = not enabled

    @work(thread=True)
    def _load_model(self) -> None:
        try:
            if self.audio is None:
                raise RuntimeError("Audio stream is not initialized")
            self.audio.initialize()
            self.call_from_thread(self._model_ready)
        except Exception as exc:
            if self.config.device == "cuda":
                try:
                    if self.audio:
                        self.audio.shutdown()
                    self.config.device = "cpu"
                    self.call_from_thread(self._notify_cpu_fallback, str(exc))
                    if self.audio is None:
                        raise RuntimeError("Audio stream is not initialized")
                    self.audio.initialize()
                    self.call_from_thread(self._model_ready)
                    return
                except Exception as fallback_exc:
                    self.call_from_thread(self._model_failed, f"GPU load failed: {exc} | CPU fallback failed: {fallback_exc}")
                    return
            self.call_from_thread(self._model_failed, str(exc))

    def _model_ready(self) -> None:
        self.is_loading = False
        self.model_loaded = True
        mic = self.query_one("#mic", MicIndicator)
        mic.state = "idle"
        log = self.query_one("#transcript_log", RichLog)
        self.sub_title = self.config.summary()
        self._set_controls_enabled(False)
        log.write(Text.from_markup(
            f"[green]✓ Model loaded ([bold]{self.config.model}[/bold] on [bold]{self.config.device}[/bold]). Press [bold]R[/bold] to begin.[/green]"
        ))
        log.write("")

    def _notify_cpu_fallback(self, err: str) -> None:
        self.sub_title = self.config.summary()
        log = self.query_one("#transcript_log", RichLog)
        log.write(Text.from_markup(
            f"[bold dark_orange]⚠ GPU unavailable. Falling back to CPU automatically.[/bold dark_orange] [dim]{err}[/dim]"
        ))

    def _model_failed(self, err: str) -> None:
        self.is_loading = False
        self.model_loaded = False
        self._set_controls_enabled(True)
        mic = self.query_one("#mic", MicIndicator)
        mic.state = "error"
        log = self.query_one("#transcript_log", RichLog)
        log.write(Text.from_markup(f"[bold red]✗ Failed to load model:[/bold red] {err}"))

    # ── Actions ───────────────────────────────────────────────────────

    def action_toggle_listening(self) -> None:
        if not self.model_loaded:
            log = self.query_one("#transcript_log", RichLog)
            log.write(Text.from_markup("[dim]Load a model first using [bold]Load Model[/bold].[/dim]"))
            return

        if self.audio is None or self.audio.recorder is None:
            return

        mic = self.query_one("#mic", MicIndicator)

        if self.audio.is_listening:
            stream = self.query_one("#streaming_box", StreamingLine)
            pending_partial = stream.partial.strip()
            if pending_partial:
                self._append_final(pending_partial)
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

