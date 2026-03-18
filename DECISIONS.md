# Technical & Product Decisions

## Product Decisions

### Game Name: "Fretboard"
Guitar-themed but distinct from "Guitar Hero" trademark. Short, memorable, and works as both a CLI command and a brand.

### 4-Lane Layout with D/F/J/K Keys
Chose D/F/J/K over other key layouts because:
- Natural resting position for touch typists (home row adjacent)
- Two keys per hand with a gap in the middle, mimicking Guitar Hero's left/right hand split
- Comfortable for extended play sessions
- Works on all keyboard layouts (unlike arrow keys which are awkward for rhythm games)

### Three Timing Windows: Perfect/Good/OK
- Perfect: ±50ms — tight but achievable, rewarding for skilled players
- Good: ±100ms — forgiving enough for casual players to enjoy
- OK: ±150ms — catches most reasonable attempts, prevents frustration
- Miss: >150ms — clear you weren't trying for that note

### Combo Multiplier System (1x/2x/3x/4x)
- Thresholds: 0→1x, 10→2x, 30→3x, 50→4x
- Rewards consistency without making early mistakes feel unrecoverable
- 4x cap prevents runaway scores while still incentivizing long combos

### Letter Grade System (S/A/B/C/D/F)
- S rank at 95%+ accuracy gives top players something to chase
- F below 60% is the familiar academic grading everyone understands
- Provides quick emotional feedback on performance

### 5 Built-in Songs with Progressive Difficulty
- Enough variety to keep interest without overwhelming choice
- Each song teaches something new (single notes → two-lane → all lanes → speed → density)
- No real audio — the game is purely visual/rhythmic, which makes it distributable as a single file

## Technical Decisions

### Python + curses for Terminal Version
- curses is built into Python on macOS/Linux — zero external dependencies
- Provides precise control over terminal rendering
- Frame-rate-independent timing using `time.time()` for accurate rhythm gameplay
- Non-blocking input via `nodelay()` for responsive controls during gameplay

### Single HTML File for Web Version
- Matches the convention of other projects in the parent directory (maltipoo_playtime, etc.)
- Zero dependencies, zero build step — just open in a browser
- Canvas API for smooth 60fps rendering
- Web Audio API for sound generation without audio files
- Fully self-contained and deployable as a static site

### Package Structure (pip/pipx installable)
- `pyproject.toml` with `[project.scripts]` entry point → `fretboard` CLI command
- Installable via `pip install .` locally or `pipx install .` for isolation
- No external dependencies — only stdlib (curses, time, dataclasses, enum)
- Easy to share: clone + pip install, or eventually publish to PyPI

### Render Deployment (Static Site)
- `render.yaml` configured for static site deployment (cheapest/simplest option)
- Serves the `web/` directory directly — no build step needed
- Also includes a Dockerfile for alternative deployment options

### Engine Architecture
- Clean separation: `engine.py` (logic) / `renderer.py` (display) / `songs.py` (data) / `main.py` (glue)
- `GameState` dataclass holds all mutable state — easy to test, easy to reason about
- Pure functions for scoring/judging — no side effects, fully unit-testable
- `NoteState` tracks each note individually — supports partial hits, replay analysis

### Testing Strategy
- pytest with no external test dependencies
- 62 unit tests covering: timing judgments, scoring math, combo/multiplier, song validation, game state
- Song validation tests check structural integrity (sorted times, valid lanes, increasing difficulty)
- No mocking of curses (would add complexity with little value) — curses rendering is tested manually
