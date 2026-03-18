"""Terminal renderer using curses."""

import curses
import math
from typing import Optional

from .engine import GameState, HitGrade, NoteState

# How many seconds of notes are visible on screen
VISIBLE_WINDOW = 3.0

# Lane display characters
NOTE_CHAR = "█"
HIT_ZONE_CHAR = "═"
LANE_SEPARATOR = "│"
MISS_CHAR = "✗"

# Minimum terminal size
MIN_WIDTH = 60
MIN_HEIGHT = 20

TITLE_ART = r"""
  _____ ____  _____ _____ ____   ___    _    ____  ____
 |  ___|  _ \| ____|_   _| __ ) / _ \  / \  |  _ \|  _ \
 | |_  | |_) |  _|   | | |  _ \| | | |/ _ \ | |_) | | | |
 |  _| |  _ <| |___  | | | |_) | |_| / ___ \|  _ <| |_| |
 |_|   |_| \_\_____| |_| |____/ \___/_/   \_\_| \_\____/
"""

CONTROLS_TEXT = """
  ╔══════════════════════════════════╗
  ║     D   F       J   K           ║
  ║    ╔═╗ ╔═╗    ╔═╗ ╔═╗          ║
  ║    ╚═╝ ╚═╝    ╚═╝ ╚═╝          ║
  ║   Left hand    Right hand       ║
  ║                                  ║
  ║   ESC = Pause   Q = Quit        ║
  ╚══════════════════════════════════╝
"""

GRADE_ART = {
    "S": [
        " ███████ ",
        " ██      ",
        " ███████ ",
        "      ██ ",
        " ███████ ",
    ],
    "A": [
        "    █    ",
        "   █ █   ",
        "  █████  ",
        " █     █ ",
        " █     █ ",
    ],
    "B": [
        " ██████  ",
        " █     █ ",
        " ██████  ",
        " █     █ ",
        " ██████  ",
    ],
    "C": [
        "  █████  ",
        " █       ",
        " █       ",
        " █       ",
        "  █████  ",
    ],
    "D": [
        " ██████  ",
        " █     █ ",
        " █     █ ",
        " █     █ ",
        " ██████  ",
    ],
    "F": [
        " ███████ ",
        " █       ",
        " █████   ",
        " █       ",
        " █       ",
    ],
}

GRADE_LABELS = {
    "S": "SUPERSTAR!",
    "A": "AWESOME!",
    "B": "GREAT JOB!",
    "C": "NOT BAD",
    "D": "KEEP TRYING",
    "F": "OUCH...",
}

DIFFICULTY_LABELS = {
    1: "Beginner friendly",
    2: "Two-lane patterns",
    3: "All four lanes",
    4: "Fast and complex",
    5: "Absolute madness",
}

COMBO_MILESTONES = [10, 25, 50, 100, 200]


def init_colors():
    """Initialize color pairs for curses."""
    curses.start_color()
    curses.use_default_colors()

    # Lane colors: green, red, yellow, blue
    curses.init_pair(1, curses.COLOR_GREEN, -1)    # Lane 0 (D)
    curses.init_pair(2, curses.COLOR_RED, -1)      # Lane 1 (F)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)   # Lane 2 (J)
    curses.init_pair(4, curses.COLOR_BLUE, -1)     # Lane 3 (K)

    # UI colors
    curses.init_pair(5, curses.COLOR_WHITE, -1)    # Default text
    curses.init_pair(6, curses.COLOR_CYAN, -1)     # Highlight
    curses.init_pair(7, curses.COLOR_MAGENTA, -1)  # Score/combo
    curses.init_pair(8, curses.COLOR_GREEN, -1)    # Perfect
    curses.init_pair(9, curses.COLOR_YELLOW, -1)   # Good
    curses.init_pair(10, curses.COLOR_RED, -1)     # Miss

    # Hit zone background colors
    curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(12, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(13, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(14, curses.COLOR_BLACK, curses.COLOR_BLUE)

    # Flash/highlight colors (bright on dark)
    curses.init_pair(15, curses.COLOR_WHITE, curses.COLOR_GREEN)
    curses.init_pair(16, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(17, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    curses.init_pair(18, curses.COLOR_WHITE, curses.COLOR_BLUE)

    # Milestone/celebration
    curses.init_pair(19, curses.COLOR_YELLOW, -1)  # Gold


def lane_color(lane: int) -> int:
    """Get the curses color pair for a lane."""
    return curses.color_pair(lane + 1)


def lane_hit_color(lane: int) -> int:
    """Get the curses color pair for a lane's hit zone."""
    return curses.color_pair(lane + 11)


def lane_flash_color(lane: int) -> int:
    """Get bright flash color for a lane."""
    return curses.color_pair(lane + 15)


def safe_addstr(win, y: int, x: int, text: str, attr=0):
    """Safely add a string, ignoring out-of-bounds errors."""
    max_y, max_x = win.getmaxyx()
    if y < 0 or y >= max_y or x >= max_x:
        return
    available = max_x - x
    if available <= 0:
        return
    text = text[:available]
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def draw_size_warning(stdscr):
    """Draw a warning if terminal is too small."""
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    msg = f"Terminal too small! Need {MIN_WIDTH}x{MIN_HEIGHT}, have {w}x{h}"
    if h > 0 and w > len(msg):
        safe_addstr(stdscr, h // 2, (w - len(msg)) // 2, msg,
                    curses.color_pair(10) | curses.A_BOLD)
    stdscr.refresh()


def draw_title_screen(stdscr):
    """Draw the main title screen."""
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    # Title art
    lines = TITLE_ART.strip().split("\n")
    start_y = max(0, h // 2 - len(lines) - 4)
    for i, line in enumerate(lines):
        x = max(0, (w - len(line)) // 2)
        safe_addstr(stdscr, start_y + i, x, line,
                    curses.color_pair(6) | curses.A_BOLD)

    # Subtitle
    sub = "♪ Terminal Rhythm Game ♪"
    safe_addstr(stdscr, start_y + len(lines) + 1, (w - len(sub)) // 2, sub,
                curses.color_pair(7))

    # Controls preview
    ctrl_lines = CONTROLS_TEXT.strip().split("\n")
    ctrl_start = start_y + len(lines) + 3
    for i, line in enumerate(ctrl_lines):
        x = max(0, (w - len(line)) // 2)
        safe_addstr(stdscr, ctrl_start + i, x, line, curses.color_pair(5))

    # Prompts
    prompt = "Press ENTER to start  •  Q to quit"
    safe_addstr(stdscr, h - 3, (w - len(prompt)) // 2, prompt,
                curses.color_pair(6) | curses.A_BOLD)

    howto = "H = How to Play"
    safe_addstr(stdscr, h - 2, (w - len(howto)) // 2, howto,
                curses.color_pair(5))

    stdscr.refresh()


def draw_how_to_play(stdscr):
    """Draw the how-to-play help screen."""
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    title = "♪ HOW TO PLAY ♪"
    safe_addstr(stdscr, 1, (w - len(title)) // 2, title,
                curses.color_pair(6) | curses.A_BOLD)

    instructions = [
        ("", 0),
        ("Notes fall from the top of the screen.", curses.color_pair(5)),
        ("Press the matching key when they hit the line.", curses.color_pair(5)),
        ("", 0),
        ("  D   F       J   K", curses.color_pair(6) | curses.A_BOLD),
        ("  Left hand   Right hand", curses.color_pair(5)),
        ("", 0),
        ("Timing:", curses.color_pair(6) | curses.A_BOLD),
        ("  PERFECT (±50ms)  = 100 pts", curses.color_pair(8) | curses.A_BOLD),
        ("  GOOD    (±100ms) =  50 pts", curses.color_pair(9) | curses.A_BOLD),
        ("  OK      (±150ms) =  25 pts", curses.color_pair(9)),
        ("", 0),
        ("Combos:", curses.color_pair(6) | curses.A_BOLD),
        ("  10x combo = 2x multiplier", curses.color_pair(5)),
        ("  30x combo = 3x multiplier", curses.color_pair(5)),
        ("  50x combo = 4x multiplier", curses.color_pair(5)),
        ("", 0),
        ("Grades:", curses.color_pair(6) | curses.A_BOLD),
        ("  S (95%+)  A (90%+)  B (80%+)", curses.color_pair(5)),
        ("  C (70%+)  D (60%+)  F (<60%)", curses.color_pair(5)),
    ]

    start_y = 3
    for i, (text, attr) in enumerate(instructions):
        if text:
            safe_addstr(stdscr, start_y + i, (w - 50) // 2, text, attr)

    prompt = "Press ESC or ENTER to go back"
    safe_addstr(stdscr, h - 2, (w - len(prompt)) // 2, prompt,
                curses.color_pair(5))

    stdscr.refresh()


def draw_song_select(stdscr, songs: list, selected: int, high_scores: dict = None):
    """Draw the song selection screen."""
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    title = "♪ SELECT A SONG ♪"
    safe_addstr(stdscr, 1, (w - len(title)) // 2, title,
                curses.color_pair(6) | curses.A_BOLD)

    safe_addstr(stdscr, 3, (w - 48) // 2,
                "Use ↑/↓ to navigate, ENTER to play, Q to quit",
                curses.color_pair(5))

    start_y = 5
    for i, song in enumerate(songs):
        is_selected = i == selected
        y = start_y + i * 4

        # Selection indicator
        prefix = "▶ " if is_selected else "  "
        attr = curses.A_BOLD | curses.A_REVERSE if is_selected else 0

        # Song name
        name_line = f"{prefix}{song['name']}"
        safe_addstr(stdscr, y, (w - 52) // 2, name_line,
                    curses.color_pair(6 if is_selected else 5) | attr)

        # Details line
        stars = "★" * song["difficulty"] + "☆" * (5 - song["difficulty"])
        detail = f"    {song.get('artist', 'Unknown')}  |  {stars}  |  {song['bpm']} BPM"
        safe_addstr(stdscr, y + 1, (w - 52) // 2, detail,
                    curses.color_pair(7 if is_selected else 5))

        # Difficulty description
        diff_label = DIFFICULTY_LABELS.get(song["difficulty"], "")
        if is_selected and diff_label:
            safe_addstr(stdscr, y + 2, (w - 52) // 2 + 4, diff_label,
                        curses.color_pair(5) | curses.A_DIM)

        # High score
        if high_scores and song["name"] in high_scores:
            hs = high_scores[song["name"]]
            hs_text = f"    BEST: {hs['score']:,}  {hs['grade']}  {hs['accuracy']:.1f}%"
            hs_color = curses.color_pair(19 if is_selected else 9)
            safe_addstr(stdscr, y + 2, (w - 52) // 2 + 30, hs_text, hs_color)

    stdscr.refresh()


def draw_countdown(stdscr, value: int, song_name: str, fraction: float = 0.0):
    """Draw a countdown screen before song starts."""
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    if value > 0:
        text = str(value)
        attr = curses.color_pair(6) | curses.A_BOLD
    else:
        text = "GO!"
        attr = curses.color_pair(8) | curses.A_BOLD

    # Big centered number
    safe_addstr(stdscr, h // 2 - 1, (w - len(text)) // 2, text, attr)

    # Song name below
    safe_addstr(stdscr, h // 2 + 2, (w - len(song_name)) // 2, song_name,
                curses.color_pair(7))

    prompt = "Get ready!"
    safe_addstr(stdscr, h // 2 + 4, (w - len(prompt)) // 2, prompt,
                curses.color_pair(5))

    stdscr.refresh()


def draw_game(stdscr, state: GameState, current_time: float,
              last_grade: Optional[HitGrade] = None, grade_timer: float = 0,
              lane_flash: list = None, miss_markers: list = None,
              combo_milestone: str = "", milestone_timer: float = 0):
    """Draw the main game screen."""
    h, w = stdscr.getmaxyx()
    stdscr.erase()

    lane_width = 8
    total_lane_width = lane_width * 4 + 5  # 4 lanes + separators
    lane_start_x = (w - total_lane_width) // 2

    hit_zone_y = h - 4
    notes_top_y = 3

    playfield_height = hit_zone_y - notes_top_y

    if lane_flash is None:
        lane_flash = [0.0, 0.0, 0.0, 0.0]
    if miss_markers is None:
        miss_markers = []

    # Draw HUD at top
    _draw_hud(stdscr, state, w)

    # Draw lane separators
    for row in range(notes_top_y, hit_zone_y + 1):
        for i in range(5):
            x = lane_start_x + i * (lane_width + 1)
            safe_addstr(stdscr, row, x, LANE_SEPARATOR,
                        curses.color_pair(5) | curses.A_DIM)

    # Draw hit zone with optional flash
    for lane in range(4):
        x = lane_start_x + lane * (lane_width + 1) + 1
        zone_str = HIT_ZONE_CHAR * lane_width
        if lane_flash[lane] > 0.15:
            # Bright flash on recent hit
            safe_addstr(stdscr, hit_zone_y, x, zone_str,
                        lane_flash_color(lane) | curses.A_BOLD)
        else:
            safe_addstr(stdscr, hit_zone_y, x, zone_str, lane_hit_color(lane))

    # Draw lane labels below hit zone
    lane_keys = ["D", "F", "J", "K"]
    for lane in range(4):
        x = lane_start_x + lane * (lane_width + 1) + 1 + lane_width // 2
        attr = lane_color(lane) | curses.A_BOLD
        if lane_flash[lane] > 0.2:
            attr = lane_flash_color(lane) | curses.A_BOLD
        safe_addstr(stdscr, hit_zone_y + 1, x, lane_keys[lane], attr)

    # Draw notes
    for note in state.notes:
        if note.hit:
            continue

        # Draw miss marker for recently missed notes
        if note.missed:
            time_since_miss = current_time - note.time - 0.15
            if 0 < time_since_miss < 0.5:
                x = lane_start_x + note.lane * (lane_width + 1) + 1 + lane_width // 2
                alpha_ok = time_since_miss < 0.4
                if alpha_ok:
                    safe_addstr(stdscr, hit_zone_y, x, MISS_CHAR,
                                curses.color_pair(10) | curses.A_BOLD)
            continue

        # Calculate vertical position based on timing
        time_until_hit = note.time - current_time
        if time_until_hit < -0.2 or time_until_hit > VISIBLE_WINDOW:
            continue

        # Map time to screen position (0 = hit zone, VISIBLE_WINDOW = top)
        progress = 1.0 - (time_until_hit / VISIBLE_WINDOW)
        note_y = notes_top_y + int(progress * playfield_height)

        if note_y < notes_top_y or note_y >= hit_zone_y:
            continue

        x = lane_start_x + note.lane * (lane_width + 1) + 1
        note_str = NOTE_CHAR * lane_width

        # Notes near the hit zone get brighter
        if time_until_hit < 0.5:
            safe_addstr(stdscr, note_y, x, note_str,
                        lane_color(note.lane) | curses.A_BOLD | curses.A_REVERSE)
        else:
            safe_addstr(stdscr, note_y, x, note_str,
                        lane_color(note.lane) | curses.A_BOLD)

    # Draw lane flash effect (fill lane briefly on hit)
    for lane in range(4):
        if lane_flash[lane] > 0.25:
            x = lane_start_x + lane * (lane_width + 1) + 1
            # Flash a few rows near the hit zone
            flash_rows = min(3, int(lane_flash[lane] * 8))
            for row_offset in range(1, flash_rows + 1):
                fy = hit_zone_y - row_offset
                if fy >= notes_top_y:
                    safe_addstr(stdscr, fy, x, " " * lane_width,
                                lane_flash_color(lane))

    # Draw hit grade feedback
    if last_grade and (current_time - grade_timer) < 0.5:
        grade_text = last_grade.value
        grade_colors = {
            HitGrade.PERFECT: curses.color_pair(8) | curses.A_BOLD | curses.A_REVERSE,
            HitGrade.GOOD: curses.color_pair(9) | curses.A_BOLD,
            HitGrade.OK: curses.color_pair(9),
            HitGrade.MISS: curses.color_pair(10) | curses.A_BOLD,
        }
        # Make the feedback more prominent
        if last_grade == HitGrade.PERFECT:
            padded = f"  ★ {grade_text} ★  "
        elif last_grade == HitGrade.MISS:
            padded = f"  ✗ {grade_text} ✗  "
        else:
            padded = f"  {grade_text}  "
        safe_addstr(stdscr, hit_zone_y + 2, (w - len(padded)) // 2,
                    padded, grade_colors.get(last_grade, 0))

    # Draw combo milestone banner
    if combo_milestone and milestone_timer > 0:
        banner = f"  ★ {combo_milestone} ★  "
        safe_addstr(stdscr, h // 2, (w - len(banner)) // 2, banner,
                    curses.color_pair(19) | curses.A_BOLD | curses.A_REVERSE)

    # Draw miss flash (subtle red indicator at edges)
    _draw_miss_flash(stdscr, h, w, miss_markers, current_time)

    # Draw pause overlay
    if state.paused:
        _draw_pause_overlay(stdscr, h, w)

    stdscr.refresh()


def _draw_hud(stdscr, state: GameState, width: int):
    """Draw the heads-up display at the top of the screen."""
    # Song name
    safe_addstr(stdscr, 0, 2, state.song_name,
                curses.color_pair(6) | curses.A_BOLD)

    # Score (right-aligned)
    score_str = f"Score: {state.score:,}"
    safe_addstr(stdscr, 0, width - len(score_str) - 2, score_str,
                curses.color_pair(7) | curses.A_BOLD)

    # Combo and multiplier
    if state.combo > 0:
        combo_str = f"Combo: {state.combo}x"
        if state.combo >= 50:
            combo_attr = curses.color_pair(19) | curses.A_BOLD
        elif state.combo >= 10:
            combo_attr = curses.color_pair(8) | curses.A_BOLD
        else:
            combo_attr = curses.color_pair(7)
        safe_addstr(stdscr, 1, 2, combo_str, combo_attr)
    else:
        safe_addstr(stdscr, 1, 2, "Combo: -", curses.color_pair(5) | curses.A_DIM)

    # Multiplier with visual emphasis
    mult_str = f"{state.multiplier}x MULT"
    if state.multiplier >= 4:
        mult_attr = curses.color_pair(19) | curses.A_BOLD | curses.A_REVERSE
    elif state.multiplier >= 3:
        mult_attr = curses.color_pair(8) | curses.A_BOLD
    elif state.multiplier >= 2:
        mult_attr = curses.color_pair(9) | curses.A_BOLD
    else:
        mult_attr = curses.color_pair(5) | curses.A_DIM
    safe_addstr(stdscr, 1, 20, mult_str, mult_attr)

    # Progress bar
    bar_width = min(30, width - 20)
    filled = int(state.progress * bar_width)
    bar = "▓" * filled + "░" * (bar_width - filled)
    pct = f"{state.progress * 100:.0f}%"
    bar_x = width - bar_width - len(pct) - 4
    safe_addstr(stdscr, 1, bar_x, f"[{bar}] {pct}", curses.color_pair(5))

    # Separator line
    safe_addstr(stdscr, 2, 0, "─" * width, curses.color_pair(5) | curses.A_DIM)


def _draw_miss_flash(stdscr, h: int, w: int, miss_markers: list, current_time: float):
    """Draw subtle red edge indicators on recent misses."""
    for miss_time in miss_markers:
        age = current_time - miss_time
        if 0 < age < 0.2:
            # Red flash on left and right edges
            for row in range(3, h - 3):
                safe_addstr(stdscr, row, 0, "│", curses.color_pair(10) | curses.A_BOLD)
                safe_addstr(stdscr, row, w - 1, "│", curses.color_pair(10) | curses.A_BOLD)


def _draw_pause_overlay(stdscr, h: int, w: int):
    """Draw pause screen overlay."""
    # Draw box
    box_w = 30
    box_h = 7
    bx = (w - box_w) // 2
    by = h // 2 - box_h // 2

    # Clear area behind box
    for row in range(by, by + box_h):
        safe_addstr(stdscr, row, bx, " " * box_w, curses.color_pair(5))

    # Border
    safe_addstr(stdscr, by, bx, "╔" + "═" * (box_w - 2) + "╗",
                curses.color_pair(6) | curses.A_BOLD)
    for row in range(by + 1, by + box_h - 1):
        safe_addstr(stdscr, row, bx, "║", curses.color_pair(6) | curses.A_BOLD)
        safe_addstr(stdscr, row, bx + box_w - 1, "║", curses.color_pair(6) | curses.A_BOLD)
    safe_addstr(stdscr, by + box_h - 1, bx, "╚" + "═" * (box_w - 2) + "╝",
                curses.color_pair(6) | curses.A_BOLD)

    # Content
    pause_text = "PAUSED"
    safe_addstr(stdscr, by + 2, (w - len(pause_text)) // 2, pause_text,
                curses.color_pair(6) | curses.A_BOLD)

    hint1 = "ESC to resume"
    safe_addstr(stdscr, by + 4, (w - len(hint1)) // 2, hint1, curses.color_pair(5))

    hint2 = "Q to quit to menu"
    safe_addstr(stdscr, by + 5, (w - len(hint2)) // 2, hint2, curses.color_pair(5))


def draw_results(stdscr, state: GameState, is_new_high_score: bool = False):
    """Draw the results/game over screen."""
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    title = "♪ SONG COMPLETE ♪"
    safe_addstr(stdscr, 1, (w - len(title)) // 2, title,
                curses.color_pair(6) | curses.A_BOLD)

    safe_addstr(stdscr, 3, (w - len(state.song_name)) // 2, state.song_name,
                curses.color_pair(7) | curses.A_BOLD)

    # Grade - draw as ASCII art
    grade = state.final_grade
    grade_colors = {
        "S": curses.color_pair(19) | curses.A_BOLD,
        "A": curses.color_pair(8) | curses.A_BOLD,
        "B": curses.color_pair(9) | curses.A_BOLD,
        "C": curses.color_pair(9),
        "D": curses.color_pair(10),
        "F": curses.color_pair(10) | curses.A_BOLD,
    }
    grade_attr = grade_colors.get(grade, 0)

    art = GRADE_ART.get(grade, [f"  {grade}  "])
    art_start_y = 5
    for i, line in enumerate(art):
        safe_addstr(stdscr, art_start_y + i, (w - len(line)) // 2, line, grade_attr)

    # Grade label
    label = GRADE_LABELS.get(grade, "")
    safe_addstr(stdscr, art_start_y + len(art) + 1, (w - len(label)) // 2, label,
                grade_attr)

    # New high score celebration
    if is_new_high_score:
        hs_text = "★ NEW HIGH SCORE! ★"
        safe_addstr(stdscr, art_start_y + len(art) + 2, (w - len(hs_text)) // 2,
                    hs_text, curses.color_pair(19) | curses.A_BOLD | curses.A_REVERSE)

    # Stats with better visual hierarchy
    stats_y = art_start_y + len(art) + 4
    stats = [
        ("Final Score", f"{state.score:,}", curses.color_pair(7) | curses.A_BOLD),
        ("Accuracy", f"{state.accuracy:.1f}%", curses.color_pair(6) | curses.A_BOLD),
        ("Max Combo", f"{state.max_combo}x", curses.color_pair(7)),
    ]

    for i, (label_text, value, attr) in enumerate(stats):
        y = stats_y + i
        line = f"{label_text:>12s}  {value}"
        safe_addstr(stdscr, y, (w - 28) // 2, line, attr)

    # Hit breakdown with visual bar
    breakdown_y = stats_y + len(stats) + 1
    total = state.perfect_count + state.good_count + state.ok_count + state.miss_count
    hits = [
        ("PERFECT", state.perfect_count, curses.color_pair(8) | curses.A_BOLD),
        ("GOOD", state.good_count, curses.color_pair(9) | curses.A_BOLD),
        ("OK", state.ok_count, curses.color_pair(9)),
        ("MISS", state.miss_count, curses.color_pair(10) | curses.A_BOLD),
    ]

    bar_max_w = 16
    for i, (label_text, count, attr) in enumerate(hits):
        y = breakdown_y + i
        bar_w = int(count / max(total, 1) * bar_max_w)
        bar = "█" * bar_w + "░" * (bar_max_w - bar_w)
        line = f"{label_text:>8s} {count:3d}  {bar}"
        safe_addstr(stdscr, y, (w - 32) // 2, line, attr)

    # Prompt
    prompt = "ENTER = continue  •  R = replay  •  Q = quit"
    safe_addstr(stdscr, h - 2, (w - len(prompt)) // 2, prompt,
                curses.color_pair(6))

    stdscr.refresh()
