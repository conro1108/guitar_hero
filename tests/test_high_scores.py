"""Tests for high score persistence."""

import json
import os
import tempfile
from unittest.mock import patch

from fretboard.main import _load_high_scores, _save_high_score


class TestLoadHighScores:
    def test_load_missing_file(self):
        with patch("fretboard.main.HIGH_SCORES_PATH", "/tmp/_nonexistent_fretboard_test.json"):
            scores = _load_high_scores()
            assert scores == {}

    def test_load_valid_file(self):
        data = {"Test Song": {"score": 1000, "accuracy": 95.0, "grade": "S"}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            try:
                with patch("fretboard.main.HIGH_SCORES_PATH", f.name):
                    scores = _load_high_scores()
                    assert scores["Test Song"]["score"] == 1000
            finally:
                os.unlink(f.name)

    def test_load_corrupt_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not json{{{")
            f.flush()
            try:
                with patch("fretboard.main.HIGH_SCORES_PATH", f.name):
                    scores = _load_high_scores()
                    assert scores == {}
            finally:
                os.unlink(f.name)


class TestSaveHighScore:
    def test_save_new_score(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            f.flush()
            try:
                with patch("fretboard.main.HIGH_SCORES_PATH", f.name):
                    high_scores = {}
                    is_new = _save_high_score(high_scores, "Test", 500, 80.0, "B")
                    assert is_new
                    assert high_scores["Test"]["score"] == 500
                    # Verify persisted to disk
                    with open(f.name) as rf:
                        on_disk = json.load(rf)
                    assert on_disk["Test"]["score"] == 500
            finally:
                os.unlink(f.name)

    def test_higher_score_replaces(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            f.flush()
            try:
                with patch("fretboard.main.HIGH_SCORES_PATH", f.name):
                    high_scores = {"Test": {"score": 100, "accuracy": 50.0, "grade": "D"}}
                    is_new = _save_high_score(high_scores, "Test", 500, 80.0, "B")
                    assert is_new
                    assert high_scores["Test"]["score"] == 500
            finally:
                os.unlink(f.name)

    def test_lower_score_does_not_replace(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            f.flush()
            try:
                with patch("fretboard.main.HIGH_SCORES_PATH", f.name):
                    high_scores = {"Test": {"score": 500, "accuracy": 80.0, "grade": "B"}}
                    is_new = _save_high_score(high_scores, "Test", 100, 50.0, "D")
                    assert not is_new
                    assert high_scores["Test"]["score"] == 500
            finally:
                os.unlink(f.name)

    def test_accuracy_rounded(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            f.flush()
            try:
                with patch("fretboard.main.HIGH_SCORES_PATH", f.name):
                    high_scores = {}
                    _save_high_score(high_scores, "Test", 500, 87.654321, "B")
                    assert high_scores["Test"]["accuracy"] == 87.7
            finally:
                os.unlink(f.name)
