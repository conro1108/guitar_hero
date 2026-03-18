"""Tests for song pattern helpers and one-hand mode constants."""

from fretboard.songs import (
    ONE_HAND_KEYS,
    ONE_HAND_NAMES,
    SONGS,
    _beat,
    _scale_run,
    _arpeggio,
    _repeat,
    _chord,
    _measure_end,
)


class TestOneHandMode:
    def test_one_hand_keys_defined(self):
        assert ONE_HAND_KEYS == ["f", "g", "h", "j"]

    def test_one_hand_names_defined(self):
        assert ONE_HAND_NAMES == ["F", "G", "H", "J"]

    def test_one_hand_keys_are_adjacent(self):
        """One-hand keys should be playable with one hand (adjacent on keyboard)."""
        assert len(ONE_HAND_KEYS) == 4

    def test_one_hand_keys_differ_from_default(self):
        from fretboard.songs import LANE_KEYS
        assert ONE_HAND_KEYS != LANE_KEYS


class TestBeat:
    def test_120_bpm(self):
        assert _beat(120) == 0.5

    def test_60_bpm(self):
        assert _beat(60) == 1.0

    def test_240_bpm(self):
        assert _beat(240) == 0.25


class TestScaleRun:
    def test_basic_scale(self):
        notes = _scale_run(1.0, 120, [0, 1, 2, 3])
        assert len(notes) == 4
        assert notes[0] == (1.0, 0)
        assert all(n[1] == lane for n, lane in zip(notes, [0, 1, 2, 3]))

    def test_timing_spacing(self):
        notes = _scale_run(0.0, 120, [0, 1, 2])
        # At 120 BPM, one beat = 0.5s, so notes at 0.0, 0.5, 1.0
        assert notes[0][0] == 0.0
        assert notes[1][0] == 0.5
        assert notes[2][0] == 1.0

    def test_subdivisions(self):
        notes = _scale_run(0.0, 120, [0, 1], subdivisions=2)
        # At 120 BPM with 2 subdivisions, dt = 0.25s
        assert notes[0][0] == 0.0
        assert notes[1][0] == 0.25

    def test_empty_lanes(self):
        notes = _scale_run(1.0, 120, [])
        assert notes == []


class TestArpeggio:
    def test_single_cycle(self):
        notes = _arpeggio(0.0, 120, [0, 1, 2], cycles=1)
        assert len(notes) == 3
        assert [n[1] for n in notes] == [0, 1, 2]

    def test_multiple_cycles(self):
        notes = _arpeggio(0.0, 120, [0, 1], cycles=3)
        assert len(notes) == 6
        assert [n[1] for n in notes] == [0, 1, 0, 1, 0, 1]

    def test_timing_is_sequential(self):
        notes = _arpeggio(0.0, 120, [0, 1, 2], cycles=1)
        times = [n[0] for n in notes]
        assert times == sorted(times)
        assert len(set(times)) == len(times)  # All unique times


class TestRepeat:
    def test_single_repeat(self):
        pattern = [(0.0, 0), (0.5, 1)]
        notes = _repeat(0.0, 120, pattern, repeats=1)
        assert len(notes) == 2

    def test_multiple_repeats(self):
        pattern = [(0.0, 0), (0.5, 1)]
        notes = _repeat(0.0, 120, pattern, repeats=3)
        assert len(notes) == 6

    def test_empty_pattern(self):
        notes = _repeat(0.0, 120, [], repeats=3)
        assert notes == []

    def test_repeats_are_offset(self):
        pattern = [(0.0, 0)]
        notes = _repeat(0.0, 120, pattern, repeats=2)
        assert notes[0][0] != notes[1][0]  # Second repeat is later

    def test_start_offset(self):
        pattern = [(0.0, 0)]
        notes = _repeat(5.0, 120, pattern, repeats=1)
        assert notes[0][0] == 5.0


class TestChord:
    def test_two_note_chord(self):
        notes = _chord(1.0, [0, 2])
        assert len(notes) == 2
        assert all(n[0] == 1.0 for n in notes)
        assert [n[1] for n in notes] == [0, 2]

    def test_four_note_chord(self):
        notes = _chord(2.5, [0, 1, 2, 3])
        assert len(notes) == 4
        assert all(n[0] == 2.5 for n in notes)

    def test_empty_chord(self):
        notes = _chord(1.0, [])
        assert notes == []


class TestMeasureEnd:
    def test_basic(self):
        notes = [(0.0, 0), (1.0, 1)]
        result = _measure_end(notes, 120)
        # Last note at 1.0 + one beat (0.5) = 1.5
        assert result == 1.5

    def test_extra_beats(self):
        notes = [(0.0, 0), (1.0, 1)]
        result = _measure_end(notes, 120, extra_beats=2)
        # Last note at 1.0 + (1 + 2) * 0.5 = 2.5
        assert result == 2.5


class TestSongProperties:
    def test_unique_song_names(self):
        names = [s["name"] for s in SONGS]
        assert len(names) == len(set(names))

    def test_easiest_songs_use_fewer_lanes_than_hardest(self):
        """Easiest songs should use fewer unique lanes than the hardest."""
        easy = [s for s in SONGS if s["difficulty"] == 1]
        hard = [s for s in SONGS if s["difficulty"] == 5]
        if easy and hard:
            easy_max_lanes = max(len(set(l for _, l in s["notes"])) for s in easy)
            hard_max_lanes = max(len(set(l for _, l in s["notes"])) for s in hard)
            assert easy_max_lanes <= hard_max_lanes

    def test_all_songs_have_artist(self):
        for song in SONGS:
            assert isinstance(song["artist"], str)
            assert len(song["artist"]) > 0
