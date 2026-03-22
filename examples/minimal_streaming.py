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


def main() -> None:
    print("=" * 55)
    print("  Open Transcribe - Minimal Streaming (no TUI)")
    print("=" * 55)

    config = Config()
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
