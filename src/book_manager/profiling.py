"""cProfile and tracemalloc helpers."""

from __future__ import annotations

import cProfile
import pstats
import tracemalloc
from io import StringIO

from book_manager.analytics import generate_books, statistics_python, author_statistics_python
from book_manager.services import BookCatalog


def run_cprofile(count: int = 100_000) -> str:
    """Profile statistics calculation and return formatted report."""
    books = generate_books(count)
    catalog = BookCatalog(books)

    profiler = cProfile.Profile()
    profiler.enable()
    _ = catalog.author_statistics(use_numpy=False)
    _ = statistics_python(catalog.pages_list())
    profiler.disable()

    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(20)
    return stream.getvalue()


def run_tracemalloc(count: int = 100_000) -> dict[str, float]:
    """Measure peak memory while generating and analysing books."""
    tracemalloc.start()
    books = generate_books(count)
    catalog = BookCatalog(books)
    _ = catalog.author_statistics(use_numpy=False)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "current_mb": current / 1024 / 1024,
        "peak_mb": peak / 1024 / 1024,
    }


def print_memory_snapshot(count: int = 50_000) -> None:
    tracemalloc.start()
    books = generate_books(count)
    snapshot = tracemalloc.take_snapshot()
    statistics = snapshot.statistics("lineno")
    print("Top 10 memory allocations:")
    for stat in statistics[:10]:
        print(stat)
    tracemalloc.stop()


if __name__ == "__main__":
    print("=== cProfile ===")
    print(run_cprofile(50_000))
    print("\n=== tracemalloc ===")
    mem = run_tracemalloc(50_000)
    print(f"Current: {mem['current_mb']:.2f} MB")
    print(f"Peak:    {mem['peak_mb']:.2f} MB")
