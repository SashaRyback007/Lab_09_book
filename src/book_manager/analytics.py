"""Analytics, data generation, NumPy statistics and caching."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from functools import lru_cache
from typing import Any

import numpy as np

from book_manager.models import Book


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

AUTHORS = [
    "Shevchenko", "Franko", "Ukrainka", "Kotsiubynskyi", "Vynnychenko",
    "Khvylovyi", "Pidmohylnyi", "Bazhan", "Rylskyi", "Tychyna",
    "Malaniuk", "Stus", "Symonenko", "Kostenko", "Andrukhovych",
    "Zhadan", "Kurkov", "Zabuzhko", "Izdryk", "Prokhasko",
]

TITLES_PREFIX = [
    "History of", "Tales of", "Songs of", "Nights of", "Days of",
    "Shadows of", "Light of", "Path of", "Voice of", "Heart of",
]


def generate_books(count: int, seed: int = 42) -> list[Book]:
    """Generate a large catalog of synthetic books."""
    random.seed(seed)
    books: list[Book] = []
    for i in range(count):
        author = random.choice(AUTHORS)
        title = f"{random.choice(TITLES_PREFIX)} {author} {i}"
        year = random.randint(1850, 2024)
        pages = random.randint(80, 900)
        books.append(Book(title=title, author=author, year=year, pages=pages))
    return books


def books_to_pages(books: list[Book]) -> list[int]:
    return [b.pages for b in books]


def books_to_years(books: list[Book]) -> list[int]:
    return [b.year for b in books]


# ---------------------------------------------------------------------------
# Baseline (pure Python loops)
# ---------------------------------------------------------------------------

def average_pages_python(books: list[Book]) -> float:
    if not books:
        return 0.0
    total = 0
    for book in books:
        total += book.pages
    return total / len(books)


def max_pages_book_python(books: list[Book]) -> Book | None:
    if not books:
        return None
    best = books[0]
    for book in books[1:]:
        if book.pages > best.pages:
            best = book
    return best


def filter_by_year_python(books: list[Book], year_from: int, year_to: int) -> list[Book]:
    return [b for b in books if year_from <= b.year <= year_to]


def search_by_author_python(books: list[Book], author: str) -> list[Book]:
    author_lower = author.lower()
    return [b for b in books if b.author.lower() == author_lower]


def author_statistics_python(books: list[Book]) -> dict[str, dict[str, float]]:
    """Per-author: count, average_pages, min_pages, max_pages, std."""
    groups: dict[str, list[int]] = defaultdict(list)
    for book in books:
        groups[book.author].append(book.pages)

    result: dict[str, dict[str, float]] = {}
    for author, pages in groups.items():
        n = len(pages)
        avg = sum(pages) / n
        mn = min(pages)
        mx = max(pages)
        variance = sum((p - avg) ** 2 for p in pages) / n
        result[author] = {
            "count": float(n),
            "average_pages": avg,
            "min_pages": float(mn),
            "max_pages": float(mx),
            "std": math.sqrt(variance),
        }
    return result


def statistics_python(values: list[float] | list[int]) -> dict[str, float]:
    """Generic statistics for a numeric list (baseline)."""
    if not values:
        return {"average": 0.0, "minimum": 0.0, "maximum": 0.0, "std": 0.0}
    count = len(values)
    average = sum(values) / count
    minimum = min(values)
    maximum = max(values)
    variance = sum((v - average) ** 2 for v in values) / count
    return {
        "average": average,
        "minimum": float(minimum),
        "maximum": float(maximum),
        "std": math.sqrt(variance),
    }


# ---------------------------------------------------------------------------
# Heavier CPU-bound operation (for meaningful multiprocessing comparison)
# ---------------------------------------------------------------------------

def page_score(pages: int) -> float:
    """Artificial CPU-bound work on a single value."""
    value = float(pages)
    for _ in range(80):
        value = (
            math.sin(value) ** 2
            + math.cos(value) ** 2
            + math.sqrt(abs(value) + 1.0)
        )
    return value


def calculate_scores_sequential(pages_list: list[int]) -> list[float]:
    return [page_score(p) for p in pages_list]


# ---------------------------------------------------------------------------
# NumPy implementations
# ---------------------------------------------------------------------------

def statistics_numpy(values: list[float] | list[int]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        return {"average": 0.0, "minimum": 0.0, "maximum": 0.0, "std": 0.0}
    return {
        "average": float(array.mean()),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "std": float(array.std()),
    }


def average_pages_numpy(books: list[Book]) -> float:
    pages = np.array([b.pages for b in books], dtype=np.float64)
    if pages.size == 0:
        return 0.0
    return float(pages.mean())


def author_statistics_numpy(books: list[Book]) -> dict[str, dict[str, float]]:
    """Author statistics using NumPy for numeric aggregates."""
    groups: dict[str, list[int]] = defaultdict(list)
    for book in books:
        groups[book.author].append(book.pages)

    result: dict[str, dict[str, float]] = {}
    for author, pages in groups.items():
        arr = np.asarray(pages, dtype=np.float64)
        result[author] = {
            "count": float(arr.size),
            "average_pages": float(arr.mean()),
            "min_pages": float(arr.min()),
            "max_pages": float(arr.max()),
            "std": float(arr.std()),
        }
    return result


# ---------------------------------------------------------------------------
# Caching (author statistics) with explicit invalidation support
# ---------------------------------------------------------------------------

# Global version counter — increment to invalidate all cached author stats
_cache_version: int = 0


def get_cache_version() -> int:
    return _cache_version


def invalidate_author_cache() -> None:
    """Call after adding/changing books so that cached statistics become stale."""
    global _cache_version
    _cache_version += 1
    cached_author_statistics.cache_clear()


@lru_cache(maxsize=256)
def cached_author_statistics(
    author: str,
    version: int,
    # books_id is a proxy; real implementation would use a stable snapshot key
) -> dict[str, float]:
    """
    Cached per-author statistics.
    The `version` argument is part of the cache key → changing version
    effectively invalidates previous entries for that author.
    """
    # This function is intentionally thin; the real calculation is done
    # by the caller that supplies the data. For demo we keep a simple
    # placeholder that will be replaced in services.
    raise NotImplementedError(
        "Use services.get_author_statistics_cached instead"
    )


def make_cached_author_stats_func(books: list[Book]):
    """
    Factory that returns a cached function bound to a concrete book list.
    Demonstrates proper cache invalidation pattern for Lab 09.
    """
    @lru_cache(maxsize=128)
    def _inner(author: str, version: int) -> dict[str, float]:
        author_lower = author.lower()
        pages = [b.pages for b in books if b.author.lower() == author_lower]
        if not pages:
            return {
                "count": 0.0,
                "average_pages": 0.0,
                "min_pages": 0.0,
                "max_pages": 0.0,
                "std": 0.0,
            }
        stats = statistics_python(pages)
        return {
            "count": float(len(pages)),
            "average_pages": stats["average"],
            "min_pages": stats["minimum"],
            "max_pages": stats["maximum"],
            "std": stats["std"],
        }

    return _inner
