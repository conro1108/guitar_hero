"""Tests for the core game engine."""

import time
from unittest.mock import patch

import pytest

from fretboard.engine import (
    GameState,
    HitGrade,
    NoteState,
    compute_multiplier,
    create_game,
    is_song_complete,
    judge_hit,
    pause_game,
    process_hit,
    start_game,
    update_misses,
    GRADE_POINTS,
)


# --- judge_hit tests ---

class TestJudgeHit:
    def test_perfect_hit(self):
        assert judge_hit(1.0, 1.0, 0.05, 0.10, 0.15) == HitGrade.PERFECT

    def test_perfect_within_window(self):
        assert judge_hit(1.0, 1.04, 0.05, 0.10, 0.15) == HitGrade.PERFECT

    def test_good_hit(self):
        assert judge_hit(1.0, 1.08, 0.05, 0.10, 0.15) == HitGrade.GOOD

    def test_ok_hit(self):
        assert judge_hit(1.0, 1.12, 0.05, 0.10, 0.15) == HitGrade.OK

    def test_miss_too_far(self):
        assert judge_hit(1.0, 1.20, 0.05, 0.10, 0.15) is None

    def test_early_perfect(self):
        assert judge_hit(1.0, 0.96, 0.05, 0.10, 0.15) == HitGrade.PERFECT

    def test_early_good(self):
        assert judge_hit(1.0, 0.92, 0.05, 0.10, 0.15) == HitGrade.GOOD

    def test_just_outside_perfect_is_good(self):
        # Floating point: abs(1.05-1.0) slightly > 0.05
        assert judge_hit(1.0, 1.05, 0.05, 0.10, 0.15) == HitGrade.GOOD

    def test_just_outside_good_is_ok(self):
        assert judge_hit(1.0, 1.10, 0.05, 0.10, 0.15) == HitGrade.OK

    def test_exact_boundary_ok(self):
        assert judge_hit(1.0, 1.15, 0.05, 0.10, 0.15) == HitGrade.OK


# --- compute_multiplier tests ---

class TestMultiplier:
    def test_base_multiplier(self):
        assert compute_multiplier(0) == 1

    def test_2x_at_10(self):
        assert compute_multiplier(10) == 2

    def test_3x_at_30(self):
        assert compute_multiplier(30) == 3

    def test_4x_at_50(self):
        assert compute_multiplier(50) == 4

    def test_4x_above_50(self):
        assert compute_multiplier(100) == 4

    def test_1x_at_9(self):
        assert compute_multiplier(9) == 1


# --- GameState tests ---

class TestGameState:
    def _make_state(self, notes=None):
        return GameState(
            song_name="Test",
            song_duration=10.0,
            notes=notes or [],
        )

    def test_accuracy_no_notes(self):
        state = self._make_state()
        assert state.accuracy == 100.0

    def test_accuracy_all_perfect(self):
        state = self._make_state()
        state.perfect_count = 10
        assert state.accuracy == 100.0

    def test_accuracy_half_miss(self):
        state = self._make_state()
        state.perfect_count = 5
        state.miss_count = 5
        assert state.accuracy == 50.0

    def test_final_grade_s(self):
        state = self._make_state()
        state.perfect_count = 100
        assert state.final_grade == "S"

    def test_final_grade_f(self):
        state = self._make_state()
        state.miss_count = 100
        assert state.final_grade == "F"

    def test_final_grade_b(self):
        state = self._make_state()
        state.perfect_count = 80
        state.miss_count = 20
        assert state.final_grade == "B"

    def test_hit_notes_count(self):
        state = self._make_state()
        state.perfect_count = 3
        state.good_count = 2
        state.ok_count = 1
        assert state.hit_notes == 6

    def test_progress_at_start(self):
        state = self._make_state()
        assert state.progress == 0.0

    def test_progress_capped_at_one(self):
        state = self._make_state()
        state.start_time = time.time() - 20  # Way past duration
        assert state.progress == 1.0


# --- create_game tests ---

class TestCreateGame:
    def test_creates_notes(self):
        song = {"name": "Test", "notes": [(1.0, 0), (2.0, 1), (3.0, 2)]}
        state = create_game(song)
        assert len(state.notes) == 3
        assert state.song_name == "Test"

    def test_notes_sorted_by_time(self):
        song = {"name": "Test", "notes": [(3.0, 0), (1.0, 1), (2.0, 2)]}
        state = create_game(song)
        times = [n.time for n in state.notes]
        assert times == [1.0, 2.0, 3.0]

    def test_duration_set(self):
        song = {"name": "Test", "notes": [(1.0, 0), (5.0, 1)]}
        state = create_game(song)
        assert state.song_duration == 7.0  # last note + 2s buffer

    def test_initial_state(self):
        song = {"name": "Test", "notes": [(1.0, 0)]}
        state = create_game(song)
        assert state.score == 0
        assert state.combo == 0
        assert state.multiplier == 1
        assert not state.finished


# --- process_hit tests ---

class TestProcessHit:
    def _make_game_with_notes(self, notes_data):
        song = {"name": "Test", "notes": notes_data}
        state = create_game(song)
        return state

    def test_hit_correct_lane(self):
        state = self._make_game_with_notes([(1.0, 0)])
        grade = process_hit(state, 0, 1.0, 0.05, 0.10, 0.15)
        assert grade == HitGrade.PERFECT
        assert state.score == 100
        assert state.combo == 1

    def test_hit_wrong_lane(self):
        state = self._make_game_with_notes([(1.0, 0)])
        grade = process_hit(state, 1, 1.0, 0.05, 0.10, 0.15)
        assert grade is None
        assert state.score == 0

    def test_combo_increases(self):
        state = self._make_game_with_notes([(1.0, 0), (2.0, 0)])
        process_hit(state, 0, 1.0, 0.05, 0.10, 0.15)
        process_hit(state, 0, 2.0, 0.05, 0.10, 0.15)
        assert state.combo == 2

    def test_cant_hit_same_note_twice(self):
        state = self._make_game_with_notes([(1.0, 0)])
        process_hit(state, 0, 1.0, 0.05, 0.10, 0.15)
        grade = process_hit(state, 0, 1.02, 0.05, 0.10, 0.15)
        assert grade is None

    def test_multiplier_applies_to_score(self):
        # Build a 10-combo to get 2x multiplier
        notes = [(float(i), 0) for i in range(12)]
        state = self._make_game_with_notes(notes)
        for i in range(12):
            process_hit(state, 0, float(i), 0.05, 0.10, 0.15)
        # Notes 1-9 (combo 1-9): 100 each at 1x = 900
        # Notes 10-12 (combo 10-12): 100 each at 2x = 600
        assert state.score == 1500
        assert state.multiplier == 2

    def test_good_hit_gives_less_points(self):
        state = self._make_game_with_notes([(1.0, 0)])
        grade = process_hit(state, 0, 1.08, 0.05, 0.10, 0.15)
        assert grade == HitGrade.GOOD
        assert state.score == 50

    def test_hit_too_far_returns_none(self):
        state = self._make_game_with_notes([(1.0, 0)])
        grade = process_hit(state, 0, 2.0, 0.05, 0.10, 0.15)
        assert grade is None


# --- update_misses tests ---

class TestUpdateMisses:
    def test_note_missed(self):
        song = {"name": "Test", "notes": [(1.0, 0)]}
        state = create_game(song)
        missed = update_misses(state, 1.5, 0.15)
        assert len(missed) == 1
        assert state.miss_count == 1
        assert state.notes[0].missed

    def test_note_not_missed_yet(self):
        song = {"name": "Test", "notes": [(1.0, 0)]}
        state = create_game(song)
        missed = update_misses(state, 1.1, 0.15)
        assert len(missed) == 0

    def test_combo_breaks_on_miss(self):
        song = {"name": "Test", "notes": [(1.0, 0), (5.0, 0)]}
        state = create_game(song)
        process_hit(state, 0, 1.0, 0.05, 0.10, 0.15)
        assert state.combo == 1
        update_misses(state, 5.5, 0.15)
        assert state.combo == 0

    def test_hit_note_not_missed(self):
        song = {"name": "Test", "notes": [(1.0, 0)]}
        state = create_game(song)
        process_hit(state, 0, 1.0, 0.05, 0.10, 0.15)
        missed = update_misses(state, 5.0, 0.15)
        assert len(missed) == 0


# --- pause tests ---

class TestPause:
    def test_pause_toggle(self):
        song = {"name": "Test", "notes": [(1.0, 0)]}
        state = create_game(song)
        start_game(state)
        assert not state.paused
        pause_game(state)
        assert state.paused
        pause_game(state)
        assert not state.paused


# --- is_song_complete tests ---

class TestSongComplete:
    def test_not_complete_at_start(self):
        song = {"name": "Test", "notes": [(1.0, 0)]}
        state = create_game(song)
        start_game(state)
        assert not is_song_complete(state)

    def test_complete_after_duration(self):
        song = {"name": "Test", "notes": [(0.1, 0)]}
        state = create_game(song)
        state.start_time = time.time() - 10  # Way past
        assert is_song_complete(state)


# --- Grade points sanity ---

class TestGradePoints:
    def test_perfect_most_points(self):
        assert GRADE_POINTS[HitGrade.PERFECT] > GRADE_POINTS[HitGrade.GOOD]

    def test_good_more_than_ok(self):
        assert GRADE_POINTS[HitGrade.GOOD] > GRADE_POINTS[HitGrade.OK]

    def test_miss_zero_points(self):
        assert GRADE_POINTS[HitGrade.MISS] == 0
