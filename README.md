# Fretboard 🎸

A Guitar Hero-style rhythm game you can play in your terminal or browser.

## Quick Start

### Terminal

```bash
git clone https://github.com/conro1108/guitar_hero.git
cd guitar_hero
pip install -e .
fretboard
```

### Web

Open `web/index.html` in any browser. That's it — no build step, no dependencies.

Deployed version available via Render (connect the repo and it auto-deploys from `render.yaml`).

## Controls

| Key | Action |
|-----|--------|
| D, F, J, K | Hit notes in lanes 1-4 |
| ↑ / ↓ | Navigate menus |
| Enter | Select / Confirm |
| ESC | Pause / Resume |
| H | How to Play (from title screen) |
| R | Replay song (from results) |
| Q | Quit / Back |

## Songs

| Song | Difficulty | BPM | Notes |
|------|-----------|-----|-------|
| First Steps | ★☆☆☆☆ | 100 | Single notes, gentle pace |
| Steady Groove | ★★☆☆☆ | 110 | Two-lane patterns, eighth notes |
| Neon Nights | ★★★☆☆ | 120 | Syncopation, all four lanes |
| Thunder Road | ★★★★☆ | 140 | Fast runs, complex rhythms |
| Final Boss | ★★★★★ | 160 | Absolute madness |

## Scoring

- **Perfect** (±50ms): 100 pts × multiplier
- **Good** (±100ms): 50 pts × multiplier
- **OK** (±150ms): 25 pts × multiplier
- **Miss**: 0 pts, breaks combo

Combo multiplier: 1x → 2x (10 combo) → 3x (30 combo) → 4x (50 combo)

Grades: S (95%+) / A (90%+) / B (80%+) / C (70%+) / D (60%+) / F

---

## Contributing / Development Guide

### Requirements

- Python 3.9+ (terminal version)
- Any modern browser (web version)
- No external dependencies — everything is stdlib or vanilla JS

### Setup

```bash
git clone https://github.com/conro1108/guitar_hero.git
cd guitar_hero
pip install -e .    # editable install — changes take effect immediately
pytest              # run tests (62 tests, should all pass)
fretboard           # launch terminal game
```

### Project Structure

```
guitar_hero/
├── fretboard/              # Terminal game (Python + curses)
│   ├── engine.py           # Core game logic — scoring, timing, state
│   ├── renderer.py         # Curses rendering — all drawing code
│   ├── songs.py            # Song definitions and pattern helpers
│   └── main.py             # Game loop, input handling, high scores
├── web/
│   └── index.html          # Web version — fully self-contained single file
├── tests/
│   ├── test_engine.py      # Engine unit tests (timing, scoring, combos)
│   └── test_songs.py       # Song validation tests (structure, difficulty)
├── pyproject.toml          # Package config, pytest config
├── render.yaml             # Render static site deployment
├── Dockerfile              # Alternative container deployment
├── DECISIONS.md            # Why things are the way they are
└── CLAUDE.md               # AI assistant context (ignore if working manually)
```

### Architecture

The terminal version has a clean 4-file separation:

- **`engine.py`** — Pure game logic. `GameState` dataclass holds all state. Functions like `process_hit()`, `update_misses()`, `judge_hit()` are pure and testable. **If you're changing game rules or scoring, this is where to look.**

- **`renderer.py`** — All curses drawing. Takes a `GameState` and draws it. Never mutates game state. **If you're changing how things look in the terminal, edit this.**

- **`songs.py`** — Song data as `(time_seconds, lane)` tuples plus helper functions (`_beat()`, `_scale_run()`, `_arpeggio()`, `_chord()`, `_repeat()`). **If you're adding songs, this is the only file you touch.**

- **`main.py`** — Glue. Game loop, input handling, state machine (title → select → countdown → play → results), high score persistence. **If you're changing game flow or adding screens, edit this.**

The web version (`web/index.html`) is a single self-contained file with the same architecture inlined. It uses Canvas for rendering and Web Audio for sound. Edit it as one file — it's ~1200 lines.

### How to Add a New Song

**Terminal** — add to `fretboard/songs.py`:

```python
SONGS.append({
    "name": "My New Song",
    "artist": "You",
    "bpm": 120,
    "difficulty": 3,  # 1-5
    "notes": _my_song_notes(120),
})

def _my_song_notes(bpm):
    b = _beat(bpm)
    notes = []
    t = 2.0  # start 2 seconds in (gives player time to react)

    # Simple pattern: one note per beat across lanes
    for i in range(16):
        notes.append((t, i % 4))  # (time_in_seconds, lane_0_to_3)
        t += b

    return notes
```

Helper functions available:
- `_beat(bpm)` — duration of one beat in seconds
- `_scale_run(start, bpm, lanes, subdivisions)` — play lanes in sequence
- `_arpeggio(start, bpm, pattern, count, subdivision)` — cycle through a pattern
- `_chord(time, lanes)` — simultaneous notes on multiple lanes
- `_repeat(pattern, count, offset)` — repeat a pattern N times

**Web** — add a new `genSong(...)` call in `web/index.html` (search for "Song 5" to find the pattern).

After adding a song, run `pytest` — `test_songs.py` automatically validates that all songs have valid structure, sorted timing, valid lanes, and increasing difficulty.

### How to Change Game Feel

| What you want to change | Where |
|-------------------------|-------|
| Timing windows (perfect/good/ok) | `songs.py` constants + `web/index.html` constants |
| Combo thresholds | `engine.py` `MULTIPLIER_THRESHOLDS` + `web/index.html` `getMultiplier()` |
| Grade boundaries | `engine.py` `final_grade` property + `web/index.html` `GRADES` array |
| Note fall speed | `renderer.py` `VISIBLE_WINDOW` (terminal) + `web/index.html` `TRAVEL_TIME` (web) |
| Visual effects (terminal) | `renderer.py` — lane flash, miss markers, HUD |
| Visual effects (web) | `web/index.html` — particles, shake, glow |
| Audio (web only) | `web/index.html` — `playTone()`, `playMilestoneSound()`, etc. |
| High scores | `main.py` `~/.fretboard_scores.json` (terminal) / `localStorage` (web) |

### Running Tests

```bash
pytest              # run all 62 tests
pytest -v           # verbose — see each test name
pytest -x           # stop on first failure
pytest -k "combo"   # run only tests with "combo" in the name
```

Tests cover:
- Timing judgments at exact boundary values
- Scoring and multiplier math
- Combo mechanics (build, break, max tracking)
- Game state (accuracy, grading, progress)
- Note lifecycle (can't double-hit, miss detection)
- Pause timing accuracy
- Song structure validation (all 5 songs)

The engine has 100% logic coverage. Renderer and main are tested manually (curses is hard to unit test).

### Key Design Constraints

- **Zero dependencies** — terminal version uses only Python stdlib. Web version is a single HTML file. Don't add packages.
- **Two versions stay in sync** — same songs, same timing windows, same scoring. If you change a game rule, change it in both `engine.py` and `web/index.html`.
- **Songs are procedural** — built from helper functions, not hardcoded note arrays. Keeps them maintainable and consistent with BPM.

### Tips

- Always run `pytest` before pushing
- The web version is easiest to test — just refresh the browser
- Terminal version needs a terminal with color support (basically everything except very old terms)
- `pip install -e .` means your Python changes take effect immediately — no reinstall needed
- Press backtick (`` ` ``) in-game to toggle FPS debug overlay (both versions)
