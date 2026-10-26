"""Entry point — quick demo of core functionality."""

from __future__ import annotations

from book_manager.analytics import generate_books
from book_manager.services import BookCatalog
from book_manager.parallel import run_race_demo


def main() -> None:
    print("Book Manager — Lab 09 (Variant 2)")
    print("=" * 50)

    books = generate_books(5_000)
    catalog = BookCatalog(books)

    print(f"Catalog size: {len(catalog.books)}")
    print(f"Average pages (Python): {catalog.average_pages():.2f}")
    print(f"Average pages (NumPy):  {catalog.average_pages(use_numpy=True):.2f}")

    best = catalog.max_pages_book()
    if best:
        print(f"Max pages book: {best.title} ({best.pages} pages)")

    stats = catalog.author_statistics()
    print(f"Authors found: {len(stats)}")

    # Cache demo
    author = books[0].author
    s1 = catalog.get_author_statistics_cached(author)
    s2 = catalog.get_author_statistics_cached(author)
    print(f"Cached author '{author}' average: {s1['average_pages']:.2f}")

    # Race condition demo
    unsafe, safe = run_race_demo(workers=4, iterations=5_000)
    expected = 4 * 5_000
    print(f"\nRace demo (expected={expected}):")
    print(f"  unsafe counter = {unsafe}")
    print(f"  safe   counter = {safe}")


if __name__ == "__main__":
    main()
