"""Main entry point for Open Transcribe."""

# ── Workaround for "bad value(s) in fds_to_keep" ─────────────────────
# RealtimeSTT / multiprocessing pass already-closed file descriptors to
# _posixsubprocess.fork_exec(), which validates them and raises ValueError.
# Patch fork_exec() directly to filter out stale FDs (arg index 3).
import os as _os
if _os.name == "posix":
    import _posixsubprocess

    _orig_fork_exec = _posixsubprocess.fork_exec

def _safe_fork_exec(*args):
    args = list(args)
    # fds_to_keep is argument index 3 — a sorted tuple of ints
    if len(args) > 3 and isinstance(args[3], (tuple, list)):
        args[3] = tuple(fd for fd in args[3] if _is_valid_fd(fd))
    return _orig_fork_exec(*args)

def _is_valid_fd(fd):
    try:
        _os.fstat(fd)
        return True
    except (OSError, ValueError):
        return False

if _os.name == "posix":
    _posixsubprocess.fork_exec = _safe_fork_exec
# ── End workaround ────────────────────────────────────────────────────

import sys
from pathlib import Path

# Ensure project root is importable when running `python src/main.py`
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.ui.app import TranscribeApp


def main() -> None:
    config = Config()
    app = TranscribeApp(config)
    app.run()


if __name__ == "__main__":
    main()
