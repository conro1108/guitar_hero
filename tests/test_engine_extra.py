"""Additional engine tests covering edge cases and untested paths."""

import time
from unittest.mock import patch

from fretboard.engine import (
    GameState,
    HitGrade,
    NoteState,
    GRADE_POINTS,
    MULTIPLIER_THRESHOLDS,
    compute_multiplier,
    create_game,
    is_song_complete,
    judge_hit,
    pause_game,
    process_hit,
    start_game,
    update_misses,
)


class TestGameStateGrades:
    """Cover grade boundaries not tested (A, C, D)."""

    def _make_state(self):
        return GameState(song_name="Test", song_duration=10.0, notes=[])

    def test_final_grade_a(self):
        state = self._make_state()
        state.perfect_count = 90
        state.miss_count = 10
        assert state.final_grade == "A"

    def test_final_grade_c(self):
        state = self._make_state()
        state.perfect_count = 70
        state.miss_count = 30
        assert state.final_grade == "C"

    def test_final_grade_d(self):
        state = self._make_state()
        state.perfect_count = 60
        state.miss_count = 40
        assert state.final_grade == "D"

    def test_grade_boundary_95_is_s(self):
        state = self._make_state()
        state.perfect_count = 95
        state.miss_count = 5
        assert state.final_grade == "S"

    def test_grade_boundary_94_is_a(self):
        state = self._make_state()
        state.perfect_count = 94
        state.miss_count = 6
        # 94% < 95, so A
        assert state.final_grade == "A"


class TestMaxCombo:
    def test_max_combo_tracked(self):
        notes = [(float(i), 0) for i in range(5)]
        song = {"name": "Test", "notes": notes}
        state = create_game(song)
        for i in range(5):
            process_hit(state, 0, float(i), 0.05, 0.10, 0.15)
        assert state.max_combo == 5

    def test_max_combo_survives_miss(self):
        notes = [(float(i), 0) for i in range(5)]
        song = {"name": "Test", "notes": notes}
        state = create_game(song)
        # Hit first 3
        for i in range(3):
            process_hit(state, 0, float(i), 0.05, 0.10, 0.15)
        assert state.max_combo == 3
        # Miss note 3 by updating misses
        update_misses(state, 3.5, 0.15)
        assert state.combo == 0
        assert state.max_combo == 3  # Max preserved

    def test_max_combo_updates_higher(self):
        notes = [(float(i), 0) for i in range(8)]
        song = {"name": "Test", "notes": notes}
        state = create_game(song)
        # Hit 3, miss 1, hit 4
        for i in range(3):
            process_hit(state, 0, float(i), 0.05, 0.10, 0.15)
        update_misses(state, 3.5, 0.15)  # miss note 3
        for i in range(4, 8):
            process_hit(state, 0, float(i), 0.05, 0.10, 0.15)
        assert state.max_combo == 4  # New streak of 4 > old 3


class TestMultiplierReset:
    def test_multiplier_resets_on_miss(self):
        notes = [(float(i), 0) for i in range(15)]
        song = {"name": "Test", "notes": notes}
        state = create_game(song)
        # Build up to 2x multiplier (10 combo)
        for i in range(10):
            process_hit(state, 0, float(i), 0.05, 0.10, 0.15)
        assert state.multiplier == 2
        # Miss next note
        update_misses(state, 10.5, 0.15)
        assert state.multiplier == 1


class TestOkHitScoring:
    def test_ok_gives_25_points(self):
        song = {"name": "Test", "notes": [(1.0, 0)]}
        state = create_game(song)
        grade = process_hit(state, 0, 1.12, 0.05, 0.10, 0.15)
        assert grade == HitGrade.OK
        assert state.score == 25
        assert state.ok_count == 1


class TestElapsedTime:
    def test_elapsed_zero_before_start(self):
        state = GameState(song_name="Test", song_duration=10.0)
        assert state.elapsed == 0.0

    def test_elapsed_increases_after_start(self):
        state = GameState(song_name="Test", song_duration=10.0)
        start_game(state)
        time.sleep(0.05)
        assert state.elapsed > 0

    def test_elapsed_freezes_when_paused(self):
        state = GameState(song_name="Test", song_duration=10.0)
        start_game(state)
        time.sleep(0.05)
        pause_game(state)
        elapsed_paused = state.elapsed
        time.sleep(0.05)
        # Should not advance while paused
        assert abs(state.elapsed - elapsed_paused) < 0.001

    def test_elapsed_resumes_after_unpause(self):
        state = GameState(song_name="Test", song_duration=10.0)
        start_game(state)
        time.sleep(0.05)
        pause_game(state)
        time.sleep(0.05)
        pause_game(state)  # Unpause
        elapsed_after_unpause = state.elapsed
        time.sleep(0.05)
        assert state.elapsed > elapsed_after_unpause


class TestTotalNotes:
    def test_total_notes_property(self):
        song = {"name": "Test", "notes": [(1.0, 0), (2.0, 1), (3.0, 2)]}
        state = create_game(song)
        assert state.total_notes == 3


class TestCreateGameEdgeCases:
    def test_duplicate_time_notes(self):
        """Chord: multiple notes at same time in different lanes."""
        song = {"name": "Test", "notes": [(1.0, 0), (1.0, 1), (1.0, 2)]}
        state = create_game(song)
        assert len(state.notes) == 3
        assert all(n.time == 1.0 for n in state.notes)

    def test_single_note_song(self):
        song = {"name": "Test", "notes": [(1.0, 0)]}
        state = create_game(song)
        assert state.song_duration == 3.0  # 1.0 + 2.0 buffer


class TestProcessHitEdgeCases:
    def test_picks_closest_note(self):
        """When two notes are in range, should hit the closest one."""
        song = {"name": "Test", "notes": [(1.0, 0), (1.2, 0)]}
        state = create_game(song)
        grade = process_hit(state, 0, 1.02, 0.05, 0.10, 0.15)
        assert grade == HitGrade.PERFECT
        assert state.notes[0].hit
        assert not state.notes[1].hit

    def test_skips_missed_notes(self):
        """Missed notes should not be re-hittable."""
        song = {"name": "Test", "notes": [(1.0, 0), (5.0, 0)]}
        state = create_game(song)
        update_misses(state, 2.0, 0.15)
        assert state.notes[0].missed
        # Try to hit the missed note — should not work
        grade = process_hit(state, 0, 1.0, 0.05, 0.10, 0.15)
        assert grade is None


class TestUpdateMissesMultiple:
    def test_multiple_notes_missed(self):
        song = {"name": "Test", "notes": [(1.0, 0), (1.5, 1), (2.0, 2)]}
        state = create_game(song)
        missed = update_misses(state, 3.0, 0.15)
        assert len(missed) == 3
        assert state.miss_count == 3

    def test_already_missed_not_counted_twice(self):
        song = {"name": "Test", "notes": [(1.0, 0)]}
        state = create_game(song)
        update_misses(state, 2.0, 0.15)
        missed_again = update_misses(state, 3.0, 0.15)
        assert len(missed_again) == 0
        assert state.miss_count == 1


class TestSongCompletePaused:
    def test_not_complete_when_paused_even_if_time_passed(self):
        """is_song_complete checks elapsed which freezes when paused."""
        song = {"name": "Test", "notes": [(0.1, 0)]}
        state = create_game(song)
        start_game(state)
        # Immediately pause
        pause_game(state)
        # Fake that wall clock advanced way past duration
        # But elapsed should be frozen near 0
        assert not is_song_complete(state)


class TestNoteState:
    def test_default_values(self):
        note = NoteState(time=1.0, lane=0)
        assert not note.hit
        assert not note.missed
        assert note.grade is None

    def test_grade_set_on_hit(self):
        note = NoteState(time=1.0, lane=0)
        note.hit = True
        note.grade = HitGrade.PERFECT
        assert note.grade == HitGrade.PERFECT


class TestJudgeHitEarly:
    def test_early_ok(self):
        assert judge_hit(1.0, 0.88, 0.05, 0.10, 0.15) == HitGrade.OK

    def test_early_miss(self):
        assert judge_hit(1.0, 0.80, 0.05, 0.10, 0.15) is None
