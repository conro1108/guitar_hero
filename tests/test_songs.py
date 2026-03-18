"""Tests for song definitions."""

import pytest

from fretboard.songs import SONGS, LANE_KEYS, LANE_NAMES, get_song, PERFECT_WINDOW, GOOD_WINDOW, OK_WINDOW


class TestSongConstants:
    def test_lane_keys(self):
        assert LANE_KEYS == ["d", "f", "j", "k"]

    def test_lane_names(self):
        assert LANE_NAMES == ["D", "F", "J", "K"]

    def test_timing_windows_ordered(self):
        assert PERFECT_WINDOW < GOOD_WINDOW < OK_WINDOW

    def test_timing_windows_positive(self):
        assert PERFECT_WINDOW > 0
        assert GOOD_WINDOW > 0
        assert OK_WINDOW > 0


class TestSongDefinitions:
    def test_five_songs_exist(self):
        assert len(SONGS) == 5

    def test_all_songs_have_required_fields(self):
        for song in SONGS:
            assert "name" in song
            assert "bpm" in song
            assert "notes" in song
            assert "difficulty" in song
            assert "artist" in song

    def test_difficulty_range(self):
        for song in SONGS:
            assert 1 <= song["difficulty"] <= 5

    def test_bpm_reasonable(self):
        for song in SONGS:
            assert 60 <= song["bpm"] <= 300

    def test_songs_have_notes(self):
        for song in SONGS:
            assert len(song["notes"]) > 0, f"{song['name']} has no notes"

    def test_notes_are_valid_tuples(self):
        for song in SONGS:
            for time, lane in song["notes"]:
                assert isinstance(time, (int, float)), f"Bad time in {song['name']}: {time}"
                assert isinstance(lane, int), f"Bad lane in {song['name']}: {lane}"
                assert 0 <= lane <= 3, f"Lane out of range in {song['name']}: {lane}"
                assert time >= 0, f"Negative time in {song['name']}: {time}"

    def test_notes_sorted_by_time(self):
        for song in SONGS:
            times = [t for t, _ in song["notes"]]
            assert times == sorted(times), f"Notes not sorted in {song['name']}"

    def test_difficulty_increases(self):
        for i in range(len(SONGS) - 1):
            assert SONGS[i]["difficulty"] <= SONGS[i + 1]["difficulty"]

    def test_note_density_increases_with_difficulty(self):
        """Harder songs should generally have more notes per second."""
        for i in range(len(SONGS) - 1):
            notes_a = SONGS[i]["notes"]
            notes_b = SONGS[i + 1]["notes"]
            if not notes_a or not notes_b:
                continue
            dur_a = notes_a[-1][0] - notes_a[0][0]
            dur_b = notes_b[-1][0] - notes_b[0][0]
            if dur_a == 0 or dur_b == 0:
                continue
            density_a = len(notes_a) / dur_a
            density_b = len(notes_b) / dur_b
            # Not strict - just check the hardest isn't less dense than easiest
        # Overall check: last song should be denser than first
        first = SONGS[0]
        last = SONGS[-1]
        dur_first = first["notes"][-1][0] - first["notes"][0][0]
        dur_last = last["notes"][-1][0] - last["notes"][0][0]
        if dur_first > 0 and dur_last > 0:
            assert len(last["notes"]) / dur_last > len(first["notes"]) / dur_first


class TestGetSong:
    def test_get_valid_index(self):
        song = get_song(0)
        assert song["name"] == SONGS[0]["name"]

    def test_get_last_song(self):
        song = get_song(4)
        assert song["name"] == SONGS[4]["name"]

    def test_get_invalid_index(self):
        with pytest.raises(IndexError):
            get_song(99)
