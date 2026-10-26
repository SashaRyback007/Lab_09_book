"""Tests for BookCatalog service and cache invalidation."""

from __future__ import annotations

import pytest

from book_manager.analytics import generate_books
from book_manager.models import Book
from book_manager.services import BookCatalog


def test_catalog_basic():
    books = generate_books(50)
    catalog = BookCatalog(books)
    assert len(catalog.books) == 50
    assert catalog.average_pages() > 0


def test_cache_hit_and_invalidation():
    books = generate_books(200)
    catalog = BookCatalog(books)
    author = books[0].author

    s1 = catalog.get_author_statistics_cached(author)
    s2 = catalog.get_author_statistics_cached(author)
    assert s1 == s2
    assert s1["count"] > 0

    # After adding a book of the same author the cache must be invalidated
    catalog.add_book(Book("Extra Title", author, 2023, 999))
    s3 = catalog.get_author_statistics_cached(author)
    assert s3["count"] == s1["count"] + 1
    assert s3["max_pages"] >= 999
