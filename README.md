# Fretboard 🎸

A Guitar Hero-style rhythm game you can play in your terminal or browser.

## Terminal Version

Notes fall down 4 lanes. Hit **D**, **F**, **J**, **K** at the right moment to score points. Build combos for multipliers, aim for that S rank.

### Install & Play

```bash
# Clone and install
git clone <repo-url>
cd guitar_hero
pip install .

# Play!
fretboard
```

Or with pipx for isolated install:
```bash
pipx install .
fretboard
```

### Controls

| Key | Action |
|-----|--------|
| D, F, J, K | Hit notes in lanes 1-4 |
| ↑ / ↓ | Navigate menus |
| Enter | Select / Confirm |
| ESC | Pause / Resume |
| Q | Quit |

### Songs

| Song | Difficulty | BPM |
|------|-----------|-----|
| First Steps | ★☆☆☆☆ | 100 |
| Steady Groove | ★★☆☆☆ | 110 |
| Neon Nights | ★★★☆☆ | 120 |
| Thunder Road | ★★★★☆ | 140 |
| Final Boss | ★★★★★ | 160 |

## Web Version

Open `web/index.html` in any modern browser, or play the deployed version (see below).

Same gameplay, same songs, with added sound effects and visual flair.

## Deployment

The web version is configured for Render static site deployment:

```bash
# render.yaml is pre-configured
# Just connect the repo to Render and deploy
```

## Development

```bash
pip install -e .
pip install pytest

# Run tests
pytest

# Run the game
fretboard
```

## Requirements

- **Terminal**: Python 3.9+, terminal with color support (most modern terminals)
- **Web**: Any modern browser (Chrome, Firefox, Safari)

## Scoring

- **Perfect** (±50ms): 100 pts × multiplier
- **Good** (±100ms): 50 pts × multiplier
- **OK** (±150ms): 25 pts × multiplier
- **Miss**: 0 pts, breaks combo

Combo multiplier: 1x → 2x (10 combo) → 3x (30 combo) → 4x (50 combo)

Grades: S (95%+) / A (90%+) / B (80%+) / C (70%+) / D (60%+) / F
