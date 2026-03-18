"""Core game engine - scoring, timing, and game state management."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class HitGrade(Enum):
    PERFECT = "PERFECT"
    GOOD = "GOOD"
    OK = "OK"
    MISS = "MISS"


# Points awarded per grade
GRADE_POINTS = {
    HitGrade.PERFECT: 100,
    HitGrade.GOOD: 50,
    HitGrade.OK: 25,
    HitGrade.MISS: 0,
}

# Combo thresholds for multiplier
MULTIPLIER_THRESHOLDS = [(50, 4), (30, 3), (10, 2), (0, 1)]


@dataclass
class NoteState:
    """A note in the game with its timing and state."""
    time: float          # When this note should be hit (seconds from song start)
    lane: int            # Which lane (0-3)
    hit: bool = False    # Whether the player hit this note
    missed: bool = False # Whether the note was missed (passed the hit zone)
    grade: Optional[HitGrade] = None


@dataclass
class GameState:
    """Full game state for a single play session."""
    song_name: str
    song_duration: float
    notes: list = field(default_factory=list)
    score: int = 0
    combo: int = 0
    max_combo: int = 0
    multiplier: int = 1
    perfect_count: int = 0
    good_count: int = 0
    ok_count: int = 0
    miss_count: int = 0
    start_time: float = 0.0
    paused: bool = False
    pause_start: float = 0.0
    total_pause_time: float = 0.0
    finished: bool = False

    @property
    def elapsed(self) -> float:
        """Seconds elapsed since song start, accounting for pauses."""
        if self.start_time == 0:
            return 0.0
        if self.paused:
            return self.pause_start - self.start_time - self.total_pause_time
        return time.time() - self.start_time - self.total_pause_time

    @property
    def progress(self) -> float:
        """Song progress as 0.0-1.0."""
        if self.song_duration == 0:
            return 0.0
        return min(1.0, self.elapsed / self.song_duration)

    @property
    def total_notes(self) -> int:
        return len(self.notes)

    @property
    def hit_notes(self) -> int:
        return self.perfect_count + self.good_count + self.ok_count

    @property
    def accuracy(self) -> float:
        """Accuracy as percentage."""
        processed = self.hit_notes + self.miss_count
        if processed == 0:
            return 100.0
        return (self.hit_notes / processed) * 100.0

    @property
    def final_grade(self) -> str:
        """Letter grade based on accuracy."""
        acc = self.accuracy
        if acc >= 95:
            return "S"
        elif acc >= 90:
            return "A"
        elif acc >= 80:
            return "B"
        elif acc >= 70:
            return "C"
        elif acc >= 60:
            return "D"
        else:
            return "F"


def compute_multiplier(combo: int) -> int:
    """Get score multiplier based on current combo."""
    for threshold, mult in MULTIPLIER_THRESHOLDS:
        if combo >= threshold:
            return mult
    return 1


def judge_hit(note_time: float, hit_time: float, perfect_window: float,
              good_window: float, ok_window: float) -> Optional[HitGrade]:
    """Judge the timing of a hit. Returns None if too far from the note."""
    diff = abs(note_time - hit_time)
    if diff <= perfect_window:
        return HitGrade.PERFECT
    elif diff <= good_window:
        return HitGrade.GOOD
    elif diff <= ok_window:
        return HitGrade.OK
    return None


def create_game(song: dict) -> GameState:
    """Create a new game state from a song definition."""
    notes = [NoteState(time=t, lane=lane) for t, lane in song["notes"]]
    notes.sort(key=lambda n: n.time)

    # Song duration is last note time + a small buffer
    duration = max(n.time for n in notes) + 2.0 if notes else 0.0

    return GameState(
        song_name=song["name"],
        song_duration=duration,
        notes=notes,
    )


def start_game(state: GameState) -> None:
    """Start the game clock."""
    state.start_time = time.time()


def pause_game(state: GameState) -> None:
    """Toggle pause state."""
    if not state.paused:
        state.paused = True
        state.pause_start = time.time()
    else:
        state.total_pause_time += time.time() - state.pause_start
        state.paused = False


def process_hit(state: GameState, lane: int, current_time: float,
                perfect_window: float, good_window: float,
                ok_window: float) -> Optional[HitGrade]:
    """Process a key press on a lane. Returns the grade if a note was hit."""
    best_note = None
    best_diff = float("inf")

    for note in state.notes:
        if note.hit or note.missed or note.lane != lane:
            continue
        diff = abs(note.time - current_time)
        if diff < best_diff and diff <= ok_window:
            best_diff = diff
            best_note = note

    if best_note is None:
        return None

    grade = judge_hit(best_note.time, current_time, perfect_window,
                      good_window, ok_window)
    if grade is None:
        return None

    best_note.hit = True
    best_note.grade = grade

    if grade == HitGrade.MISS:
        state.combo = 0
        state.miss_count += 1
    else:
        state.combo += 1
        state.max_combo = max(state.max_combo, state.combo)
        state.multiplier = compute_multiplier(state.combo)
        points = GRADE_POINTS[grade] * state.multiplier
        state.score += points

        if grade == HitGrade.PERFECT:
            state.perfect_count += 1
        elif grade == HitGrade.GOOD:
            state.good_count += 1
        elif grade == HitGrade.OK:
            state.ok_count += 1

    return grade


def update_misses(state: GameState, current_time: float, ok_window: float) -> list:
    """Mark notes that have passed the hit zone as missed. Returns newly missed notes."""
    newly_missed = []
    for note in state.notes:
        if not note.hit and not note.missed:
            if current_time - note.time > ok_window:
                note.missed = True
                note.grade = HitGrade.MISS
                state.miss_count += 1
                state.combo = 0
                state.multiplier = 1
                newly_missed.append(note)
    return newly_missed


def is_song_complete(state: GameState) -> bool:
    """Check if the song is over."""
    return state.elapsed >= state.song_duration
