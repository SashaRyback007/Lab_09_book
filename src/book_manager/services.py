"""High-level services: catalog operations, caching with invalidation."""

from __future__ import annotations

from book_manager.analytics import (
    author_statistics_python,
    author_statistics_numpy,
    average_pages_python,
    average_pages_numpy,
    filter_by_year_python,
    max_pages_book_python,
    search_by_author_python,
    statistics_python,
    statistics_numpy,
    make_cached_author_stats_func,
    get_cache_version,
    invalidate_author_cache,
)
from book_manager.models import Book


class BookCatalog:
    """In-memory book catalog with profiling-friendly operations."""

    def __init__(self, books: list[Book] | None = None) -> None:
        self._books: list[Book] = list(books) if books else []
        self._cached_author_stats = make_cached_author_stats_func(self._books)

    @property
    def books(self) -> list[Book]:
        return self._books

    def add_book(self, book: Book) -> None:
        self._books.append(book)
        # Invalidate caches because data changed
        invalidate_author_cache()
        self._cached_author_stats = make_cached_author_stats_func(self._books)

    def search_by_author(self, author: str) -> list[Book]:
        return search_by_author_python(self._books, author)

    def filter_by_year(self, year_from: int, year_to: int) -> list[Book]:
        return filter_by_year_python(self._books, year_from, year_to)

    def max_pages_book(self) -> Book | None:
        return max_pages_book_python(self._books)

    def average_pages(self, use_numpy: bool = False) -> float:
        if use_numpy:
            return average_pages_numpy(self._books)
        return average_pages_python(self._books)

    def author_statistics(self, use_numpy: bool = False) -> dict:
        if use_numpy:
            return author_statistics_numpy(self._books)
        return author_statistics_python(self._books)

    def get_author_statistics_cached(self, author: str) -> dict[str, float]:
        """Returns cached statistics for one author (version-aware)."""
        version = get_cache_version()
        return self._cached_author_stats(author, version)

    def pages_list(self) -> list[int]:
        return [b.pages for b in self._books]
