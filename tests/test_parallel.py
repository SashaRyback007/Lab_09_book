"""Tests for parallel modules and race-condition fix."""

from __future__ import annotations

import pytest

from book_manager.analytics import calculate_scores_sequential, page_score
from book_manager.parallel import (
    calculate_scores_threads,
    calculate_scores_processes,
    run_race_demo,
    get_counter,
    reset_counter,
)


def test_page_score_deterministic():
    assert page_score(100) == page_score(100)


def test_scores_threads_match_sequential():
    values = [70, 80, 90, 100, 110]
    seq = calculate_scores_sequential(values)
    thr = calculate_scores_threads(values, workers=2)
    assert thr == seq


def test_scores_processes_match_sequential():
    values = [70, 80, 90, 100]
    seq = calculate_scores_sequential(values)
    proc = calculate_scores_processes(values, workers=2)
    assert proc == seq


def test_race_condition_demo():
    """Unsafe counter is often wrong; safe counter must be exact."""
    unsafe, safe = run_race_demo(workers=4, iterations=3_000)
    expected = 4 * 3_000
    assert safe == expected
    # unsafe may or may not be equal; we only assert safe is correct
    assert unsafe <= expected
