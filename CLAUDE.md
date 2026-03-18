# CLAUDE.md — Fretboard

## What This Is

"Fretboard" — a Guitar Hero-style rhythm game with two versions:
- **Terminal**: Python + curses, installed via `pip install .`, run with `fretboard`
- **Web**: Single-file HTML app in `web/index.html`, deployable as static site on Render

## Commands

```bash
pip install -e .    # Install in dev mode
pytest              # Run tests (62 tests)
fretboard           # Launch terminal game
```

## Architecture

- `fretboard/engine.py` — Core game logic (scoring, timing, state)
- `fretboard/renderer.py` — Curses-based terminal rendering
- `fretboard/songs.py` — Song definitions and timing constants
- `fretboard/main.py` — Game loop and input handling
- `web/index.html` — Self-contained web version
- `tests/` — pytest test suite

## Key Design Points

- Zero external dependencies (stdlib only)
- 4 lanes: D/F/J/K keys
- Timing: Perfect ±50ms, Good ±100ms, OK ±150ms
- Songs defined as `(time_seconds, lane)` tuples
