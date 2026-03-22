# Open Transcribe

A beautiful, open-source, **CPU-only** real-time speech-to-text app for your terminal — inspired by [Wispr Flow](https://wisprflow.ai).

```
┌─ Open Transcribe ─────────────────────────────────────────────┐
│  ● LISTENING — speak now                                 │
├──────────────────────────────────────────────────────────┤
│  The quick brown fox jumps over▌                         │  ← live streaming
├──────────────────────────────────────────────────────────┤
│  14:02:31  The quick brown fox jumps over the lazy dog.  │  ← locked-in
│  14:02:28  Hello world, this is Open Transcribe.              │
│  14:02:25  ✓ Model loaded.  Press R to begin.            │
└──────────────────────────────────────────────────────────┘
```

## Features

- **Real-time streaming** — words appear as you speak (like watching an LLM type)
- **Full transcription** — partial text streams in, then the full sentence locks in when you pause
- **CPU-only** — no GPU required, runs on any laptop
- **Cross-platform** — Windows, macOS, Linux
- **Gorgeous TUI** — dark theme terminal UI built with Textual
- **Minimal footprint** — ~150 MB model download, low RAM usage

## Quick Start

```bash
# 1. Clone & enter
cd open_transcribe

# 2. Create a virtual environment
python -m venv stt_env

# 3. Activate it
#    Windows:
stt_env\Scripts\activate
#    macOS / Linux: (Can skip the following on Windows and directly do pip install -r requirements.txt)
source stt_env/bin/activate
sudo brew install portaudio # macOS 
sudo apt-get update # Linux
sudo apt-get install python3-dev portaudio19-dev # Linux

# 4. Install dependencies
pip install -r requirements.txt
```

## Usage

### Terminal UI (recommended)

```bash
python src/main.py
```

| Key       | Action              |
|-----------|---------------------|
| `R`       | Toggle recording    |
| `C`       | Clear transcript    |
| `Q`       | Quit                |

The TUI has two zones:
- **Top box** — live streaming partial text (updates as you speak)
- **Bottom log** — finalized, timestamped sentences (appear when you pause for ~1 sec)

### Minimal CLI (no UI)

```bash
python examples/minimal_streaming.py
```

Prints streaming partials and final sentences directly in your terminal. Great for debugging or piping output.

### Super Simple (bare-bones test)

```bash
python examples/super_simple.py
```

Absolute minimum script — useful to verify your microphone and model work before using the TUI.

## Architecture

```
Mic → RealtimeSTT (VAD + Silero) → faster-whisper (CPU, float32) → Callbacks → TUI
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
| `cublas64_12.dll not found` | You're accidentally hitting GPU mode. The app forces `device="cpu"` + `compute_type="float32"` to avoid this. Make sure you're on the latest code. |
| No audio / silent | Check OS microphone privacy settings. On Windows: Settings → Privacy → Microphone → allow Python. |
| `webrtcvad` install fails | Install Visual Studio C++ Build Tools (Windows) or `build-essential` (Linux). |
| Model download hangs | First run downloads ~150 MB from Hugging Face. Ensure internet access. Subsequent runs are cached. |

## License

MIT
