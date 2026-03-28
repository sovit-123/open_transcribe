# Open Transcribe

A beautiful, open-source real-time speech-to-text app for your terminal - inspired by [Wispr Flow](https://wisprflow.ai).

```
┌─ Open Transcribe ────────────────────────────────────────┐
│  ● LISTENING — speak now                                 │
├──────────────────────────────────────────────────────────┤
│  The quick brown fox jumps over▌                         │  ← live streaming
├──────────────────────────────────────────────────────────┤
│  14:02:31  The quick brown fox jumps over the lazy dog.  │  ← locked-in
│  14:02:28  Hello world, this is Open Transcribe.         │
│  14:02:25  ✓ Model loaded.  Press R to begin.            │
└──────────────────────────────────────────────────────────┘
```

## Features

**Built on top of [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT).**

- **Real-time streaming** - words appear as you speak (like watching an LLM type)
- **Full transcription** - partial text streams in, then the full sentence locks in when you pause
- **Runtime model + device selection** - choose model and CPU/GPU at app startup
- **CPU fallback** - if CUDA load fails, the app automatically falls back to CPU
- **Cross-platform** - Windows, macOS, Linux
- **Optional type-to-cursor mode** - transcribed text can be typed into the active app
- **Gorgeous TUI** - dark theme terminal UI built with Textual
- **Minimal footprint** - ~150 MB model download, low RAM usage

## Quick Start

```bash
# 1. Clone & enter
cd open_transcribe


# 2. Create a virtual environment
python -m venv stt_env


# 3. Activate it
#    Windows:
stt_env\Scripts\activate
pip install -r requirements.txt

#    macOS / Linux: (Can skip the following on Windows and directly do pip install -r requirements.txt)
source stt_env/bin/activate
sudo brew install portaudio # macOS 
sudo apt-get update && sudo apt-get install python3-dev portaudio19-dev # Linux


# 4. Install dependencies
pip install -r requirements.txt
```

## Usage

### Terminal UI (recommended)

```bash
python src/main.py

# Optional: type finalized text into active cursor
python src/main.py --type-text
```

| Key       | Action              |
|-----------|---------------------|
| `R`       | Toggle recording    |
| `C`       | Clear transcript    |
| `Q`       | Quit                |

On startup, use the top controls to choose:
- **Model** (from a safe built-in list)
- **Device** (`CPU` or `GPU (CUDA)`)

Then press **Load Model** before recording.

If `GPU (CUDA)` is selected but unavailable, the app automatically retries on CPU and shows a bold orange status message.

The TUI has two zones:
- **Top box** — live streaming partial text (updates as you speak)
- **Bottom log** — finalized, timestamped sentences (appear when you pause for ~1 sec)

### Minimal CLI (no UI)

```bash
python examples/minimal_streaming.py
```

Prints streaming partials and final sentences directly in your terminal. Great for debugging or piping output.

### Dictation to active cursor

```bash
pip install pyautogui
python examples/type_to_cursor.py
```

This mode types finalized phrases into whichever window currently has keyboard focus.

## Architecture

```
Mic → RealtimeSTT (VAD + Silero) → faster-whisper (CPU/GPU, float32) → Callbacks → TUI
```

| Layer         | Library           |
|---------------|-------------------|
| Audio capture | sounddevice       |
| VAD           | Silero VAD        |
| STT model     | faster-whisper    |
| Streaming     | RealtimeSTT       |
| TUI           | Textual + Rich    |

Default model: `base` (~150 MB, ~1 GB RAM, great accuracy for English).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| CUDA / GPU library error (`cublas...`, `libcuda...`) | If GPU loading fails, the app automatically falls back to CPU and logs a warning in orange. |
| No audio / silent | Check OS microphone privacy settings. On Windows: Settings → Privacy → Microphone → allow Python. |
| `webrtcvad` install fails | Install Visual Studio C++ Build Tools (Windows) or `build-essential` (Linux). |
| Model download hangs | First run downloads ~150 MB from Hugging Face. Ensure internet access. Subsequent runs are cached. |

## License

MIT

## Acknowledgement

* [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT)
