"""Minimal dictation-to-cursor example.

This runs without the Textual UI and types finalized speech directly into
whatever app/window currently has keyboard focus.

Usage:
    python examples/type_to_cursor.py

Requirements:
    pip install pyautogui
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audio_stream import AudioStream
from src.config import Config


def main() -> None:
    config = Config(type_text=True, type_text_append_space=True)

    print("=" * 60)
    print("Open Transcribe - Type to Cursor")
    print("=" * 60)
    print("This script will type finalized speech at your active cursor.")
    print("After start, switch focus to your target editor/chat app.")

    def on_realtime(text: str) -> None:
        print(f"  ✎ {text}".ljust(80), end="\r", flush=True)

    def on_final(text: str) -> None:
        print(f"\n  ✅ {text}")

    def on_error(err: str) -> None:
        print(f"\n  ⚠ ERROR: {err}", file=sys.stderr)

    stream = AudioStream(
        config=config,
        on_realtime=on_realtime,
        on_final=on_final,
        on_error=on_error,
    )

    try:
        stream.initialize()
        print("\nModel loaded. Starting microphone now...")
        print("Switch to your target window. Press Ctrl+C here to stop.\n")
        stream.start()

        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stream.shutdown()
        print("Goodbye!")


if __name__ == "__main__":
    main()
