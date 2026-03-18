"""Main entry point - game loop and input handling."""

import curses
import json
import os
import sys
import time

from .engine import (
    HitGrade,
    create_game,
    is_song_complete,
    pause_game,
    process_hit,
    start_game,
    update_misses,
)
from .renderer import (
    COMBO_MILESTONES,
    MIN_HEIGHT,
    MIN_WIDTH,
    draw_countdown,
    draw_game,
    draw_how_to_play,
    draw_results,
    draw_size_warning,
    draw_song_select,
    draw_title_screen,
    init_colors,
)
from .songs import LANE_KEYS, ONE_HAND_KEYS, ONE_HAND_NAMES, OK_WINDOW, GOOD_WINDOW, PERFECT_WINDOW, SONGS

# Target frame rate
TARGET_FPS = 60
FRAME_TIME = 1.0 / TARGET_FPS

# High scores file
HIGH_SCORES_PATH = os.path.expanduser("~/.fretboard_scores.json")


def _load_high_scores() -> dict:
    """Load high scores from disk."""
    try:
        with open(HIGH_SCORES_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_high_score(high_scores: dict, song_name: str, score: int,
                     accuracy: float, grade: str) -> bool:
    """Save a high score if it beats the existing one. Returns True if new high score."""
    existing = high_scores.get(song_name)
    is_new = existing is None or score > existing.get("score", 0)
    if is_new:
        high_scores[song_name] = {
            "score": score,
            "accuracy": round(accuracy, 1),
            "grade": grade,
        }
        try:
            with open(HIGH_SCORES_PATH, "w") as f:
                json.dump(high_scores, f, indent=2)
        except OSError:
            pass
    return is_new


def _check_size(stdscr) -> bool:
    """Check if terminal is large enough."""
    h, w = stdscr.getmaxyx()
    return h >= MIN_HEIGHT and w >= MIN_WIDTH


def _title_screen(stdscr) -> str:
    """Show title screen. Returns 'play', 'howto', or 'quit'."""
    while True:
        if not _check_size(stdscr):
            draw_size_warning(stdscr)
            curses.napms(500)
            continue

        draw_title_screen(stdscr)
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            return "quit"
        if key in (curses.KEY_ENTER, 10, 13):
            return "play"
        if key in (ord("h"), ord("H")):
            return "howto"
        curses.napms(50)


def _how_to_play(stdscr):
    """Show how-to-play screen."""
    while True:
        if not _check_size(stdscr):
            draw_size_warning(stdscr)
            curses.napms(500)
            continue

        draw_how_to_play(stdscr)
        key = stdscr.getch()
        if key in (27, curses.KEY_ENTER, 10, 13):  # ESC or ENTER
            return
        curses.napms(50)


def _song_select(stdscr, high_scores: dict, one_hand_mode: bool = False) -> tuple:
    """Show song selection. Returns (song_index, one_hand_mode) or (-1, one_hand_mode) to quit."""
    selected = 0
    while True:
        if not _check_size(stdscr):
            draw_size_warning(stdscr)
            curses.napms(500)
            continue

        draw_song_select(stdscr, SONGS, selected, high_scores, one_hand_mode)
        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            return -1, one_hand_mode
        elif key == 9:  # Tab key
            one_hand_mode = not one_hand_mode
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(SONGS)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(SONGS)
        elif key in (curses.KEY_ENTER, 10, 13):
            return selected, one_hand_mode

        curses.napms(50)


def _countdown(stdscr, song_index: int) -> bool:
    """Show 3-2-1-GO countdown. Returns True to proceed, False if ESC pressed."""
    song = SONGS[song_index]
    for value in [3, 2, 1, 0]:
        start = time.time()
        text = song["name"]
        while time.time() - start < 0.7:
            if not _check_size(stdscr):
                draw_size_warning(stdscr)
                curses.napms(100)
                continue

            fraction = (time.time() - start) / 0.7
            draw_countdown(stdscr, value, text, fraction)

            # Check for ESC to cancel
            stdscr.nodelay(True)
            try:
                key = stdscr.getch()
                if key == 27:
                    stdscr.nodelay(False)
                    return False
            except curses.error:
                pass
            stdscr.nodelay(False)

            curses.napms(16)
    return True


def _play_song(stdscr, song_index: int, high_scores: dict,
               one_hand_mode: bool = False) -> str:
    """Play a song. Returns 'menu', 'replay', or 'quit'."""
    song = SONGS[song_index]

    # Select keys based on mode
    active_keys = ONE_HAND_KEYS if one_hand_mode else LANE_KEYS
    key_labels = ONE_HAND_NAMES if one_hand_mode else ["D", "F", "J", "K"]

    # Countdown
    if not _countdown(stdscr, song_index):
        return "menu"

    state = create_game(song)
    start_game(state)

    last_grade = None
    grade_timer = 0.0
    lane_flash = [0.0, 0.0, 0.0, 0.0]
    miss_markers = []  # timestamps of recent misses
    combo_milestone = ""
    milestone_timer = 0.0
    prev_combo = 0

    # Use nodelay for non-blocking input during gameplay
    stdscr.nodelay(True)

    try:
        while True:
            frame_start = time.time()
            current_time = state.elapsed

            # Check for song completion
            if is_song_complete(state) and not state.paused:
                state.finished = True
                break

            # Process input
            try:
                key = stdscr.getch()
            except curses.error:
                key = -1

            if key != -1:
                if key == 27:  # ESC
                    pause_game(state)
                elif key in (ord("q"), ord("Q")):
                    if state.paused:
                        return "menu"
                    return "menu"
                elif not state.paused:
                    # Check lane keys
                    char = chr(key).lower() if 0 <= key < 256 else ""
                    if char in active_keys:
                        lane = active_keys.index(char)
                        prev_combo = state.combo
                        grade = process_hit(state, lane, current_time,
                                            PERFECT_WINDOW, GOOD_WINDOW,
                                            OK_WINDOW)
                        if grade:
                            last_grade = grade
                            grade_timer = current_time
                            # Set lane flash based on grade
                            if grade == HitGrade.PERFECT:
                                lane_flash[lane] = 0.4
                            elif grade == HitGrade.GOOD:
                                lane_flash[lane] = 0.25
                            elif grade == HitGrade.OK:
                                lane_flash[lane] = 0.15

                            # Check combo milestones
                            for m in COMBO_MILESTONES:
                                if prev_combo < m <= state.combo:
                                    combo_milestone = f"{m}x COMBO!"
                                    milestone_timer = 1.0
                                    break

            # Update missed notes
            if not state.paused:
                missed = update_misses(state, current_time, OK_WINDOW)
                if missed:
                    last_grade = HitGrade.MISS
                    grade_timer = current_time
                    miss_markers.append(current_time)
                    # Keep only recent miss markers
                    miss_markers = [t for t in miss_markers if current_time - t < 0.3]

            # Decay lane flashes
            dt = FRAME_TIME
            for i in range(4):
                if lane_flash[i] > 0:
                    lane_flash[i] = max(0, lane_flash[i] - dt)
            if milestone_timer > 0:
                milestone_timer = max(0, milestone_timer - dt)

            # Check terminal size
            if not _check_size(stdscr):
                draw_size_warning(stdscr)
                if not state.paused:
                    pause_game(state)
                curses.napms(100)
                continue

            # Render
            draw_game(stdscr, state, current_time, last_grade, grade_timer,
                      lane_flash, miss_markers, combo_milestone, milestone_timer,
                      key_labels=key_labels)

            # Frame rate limiting
            elapsed_frame = time.time() - frame_start
            sleep_time = FRAME_TIME - elapsed_frame
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        stdscr.nodelay(False)

    # Save high score
    is_new_hs = _save_high_score(
        high_scores, song["name"], state.score, state.accuracy, state.final_grade
    )

    # Show results
    return _results_screen(stdscr, state, is_new_hs)


def _results_screen(stdscr, state, is_new_high_score: bool = False) -> str:
    """Show results. Returns 'menu', 'replay', or 'quit'."""
    while True:
        if not _check_size(stdscr):
            draw_size_warning(stdscr)
            curses.napms(500)
            continue

        draw_results(stdscr, state, is_new_high_score)
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            return "quit"
        if key in (curses.KEY_ENTER, 10, 13):
            return "menu"
        if key in (ord("r"), ord("R")):
            return "replay"
        curses.napms(50)


def _game_loop(stdscr):
    """Main game loop."""
    # Setup curses
    curses.curs_set(0)  # Hide cursor
    init_colors()
    stdscr.timeout(100)

    high_scores = _load_high_scores()

    # Title screen
    while True:
        result = _title_screen(stdscr)
        if result == "quit":
            return
        if result == "howto":
            _how_to_play(stdscr)
            continue
        break  # "play"

    one_hand_mode = False

    # Main loop: song select -> play -> results -> repeat
    while True:
        song_index, one_hand_mode = _song_select(stdscr, high_scores, one_hand_mode)
        if song_index == -1:
            return

        while True:
            result = _play_song(stdscr, song_index, high_scores, one_hand_mode)
            if result == "replay":
                # Replay same song
                high_scores = _load_high_scores()  # Refresh
                continue
            elif result == "quit":
                return
            else:
                # Back to menu
                high_scores = _load_high_scores()  # Refresh
                break


def main():
    """Entry point."""
    try:
        curses.wrapper(_game_loop)
    except KeyboardInterrupt:
        pass
    print("Thanks for playing Fretboard! 🎸")


if __name__ == "__main__":
    main()
