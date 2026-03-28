"""Minimal streaming example — no TUI, just plain terminal output.

Demonstrates real-time partial transcription + final locked-in text.
Same engine as the full TUI app, zero UI overhead.

Usage:
    python examples/minimal_streaming.py
"""

import sys
from pathlib import Path

# Make `src` importable when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

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


def _prompt_choice(title: str, choices: list[tuple[str, str]], default_index: int = 0) -> str:
    print(title)
    for idx, (label, _) in enumerate(choices, start=1):
        default_marker = " (default)" if (idx - 1) == default_index else ""
        print(f"  {idx}. {label}{default_marker}")

    prompt = f"Select [1-{len(choices)}] (Enter for default): "
    while True:
        try:
            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nUsing default selection.")
            return choices[default_index][1]

        if not user_input:
            return choices[default_index][1]

        if user_input.isdigit():
            selected_index = int(user_input) - 1
            if 0 <= selected_index < len(choices):
                return choices[selected_index][1]

        lowered_input = user_input.lower()
        for label, value in choices:
            if lowered_input in {label.lower(), value.lower()}:
                return value

        print("Invalid choice. Please enter a number from the list, or press Enter for default.")


def main() -> None:
    print("=" * 55)
    print("  Open Transcribe - Minimal Streaming (no TUI)")
    print("=" * 55)

    config = Config()

    default_model_index = SAFE_MODELS.index(config.model) if config.model in SAFE_MODELS else 2
    model_choices = [(model, model) for model in SAFE_MODELS]
    device_choices = [("CPU", "cpu"), ("GPU (CUDA)", "cuda")]
    default_device_index = 1 if config.device == "cuda" else 0

    print("\nChoose launch options:\n")
    config.model = _prompt_choice("Model:", model_choices, default_model_index)
    config.device = _prompt_choice("Device:", device_choices, default_device_index)
    print()

    print(f"  {config.summary()}")
    print("-" * 55)
    print("Initializing model (first run downloads the model)…\n")

    def on_realtime(text: str) -> None:
        # Overwrite the same line with partial text
        print(f"  ✎  {text}".ljust(80), end="\r", flush=True)

    def on_final(text: str) -> None:
        # Lock in the final sentence on a new line
        print(f"\n  ✅  {text}\n")

    def on_error(err: str) -> None:
        print(f"\n  ⚠  ERROR: {err}\n", file=sys.stderr)

    stream = AudioStream(
        config=config,
        on_realtime=on_realtime,
        on_final=on_final,
        on_error=on_error,
    )

    try:
        stream.initialize()
        print("Model loaded!  Speak now (Ctrl+C to quit).\n")
        stream.start()

        # Block main thread
        import time
        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nStopping…")
        stream.shutdown()
        print("Goodbye!")


if __name__ == "__main__":
    main()
