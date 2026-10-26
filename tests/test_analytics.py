"""Tests for analytics and statistics correctness."""

from __future__ import annotations

import math

import pytest

from book_manager.analytics import (
    generate_books,
    statistics_python,
    statistics_numpy,
    average_pages_python,
    average_pages_numpy,
    author_statistics_python,
    author_statistics_numpy,
    max_pages_book_python,
    search_by_author_python,
    filter_by_year_python,
)
from book_manager.models import Book


def test_generate_books_count():
    books = generate_books(100)
    assert len(books) == 100
    assert all(isinstance(b, Book) for b in books)


def test_statistics_python_numpy_match():
    values = [70.0, 80.0, 90.0, 100.0, 85.5]
    py = statistics_python(values)
    np_ = statistics_numpy(values)
    assert np_["average"] == pytest.approx(py["average"])
    assert np_["minimum"] == pytest.approx(py["minimum"])
    assert np_["maximum"] == pytest.approx(py["maximum"])
    assert np_["std"] == pytest.approx(py["std"], rel=1e-9)


def test_average_pages():
    books = [
        Book("A", "Author1", 2000, 100),
        Book("B", "Author1", 2001, 200),
        Book("C", "Author2", 2002, 300),
    ]
    assert average_pages_python(books) == pytest.approx(200.0)
    assert average_pages_numpy(books) == pytest.approx(200.0)


def test_max_pages_book():
    books = [
        Book("A", "X", 2000, 100),
        Book("B", "Y", 2001, 500),
        Book("C", "Z", 2002, 300),
    ]
    best = max_pages_book_python(books)
    assert best is not None
    assert best.pages == 500
    assert best.title == "B"


def test_search_by_author():
    books = generate_books(200)
    author = books[0].author
    found = search_by_author_python(books, author)
    assert all(b.author == author for b in found)
    assert len(found) > 0


def test_filter_by_year():
    books = generate_books(300)
    filtered = filter_by_year_python(books, 1950, 2000)
    assert all(1950 <= b.year <= 2000 for b in filtered)


def test_author_statistics_consistency():
    books = generate_books(500)
    py = author_statistics_python(books)
    np_ = author_statistics_numpy(books)
    assert set(py.keys()) == set(np_.keys())
    for author in py:
        assert np_[author]["average_pages"] == pytest.approx(
            py[author]["average_pages"], rel=1e-9
        )
        assert np_[author]["count"] == py[author]["count"]
