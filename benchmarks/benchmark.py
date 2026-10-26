"""
Main experimental benchmark for Lab 09 — Variant 2 (Book Catalog).

Compares:
  - Baseline Python loops
  - ThreadPoolExecutor
  - ProcessPoolExecutor
  - NumPy vectorization
  - Caching (cold vs warm)
  - I/O-bound parallel file loading

Produces a summary table and writes results to CSV.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Callable, Any

# Make src importable when running from project root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from book_manager.analytics import (
    generate_books,
    statistics_python,
    statistics_numpy,
    calculate_scores_sequential,
    author_statistics_python,
    author_statistics_numpy,
    make_cached_author_stats_func,
    invalidate_author_cache,
    get_cache_version,
)
from book_manager.parallel import (
    calculate_scores_threads,
    calculate_scores_processes,
    load_files_parallel,
    load_files_sequential,
)
from book_manager.services import BookCatalog
from book_manager.models import Book


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def benchmark_repeated(
    func: Callable,
    *args: Any,
    repeats: int = 5,
    **kwargs: Any,
) -> float:
    times: list[float] = []
    for _ in range(repeats):
        start = perf_counter()
        func(*args, **kwargs)
        times.append(perf_counter() - start)
    return mean(times)


def calculate_speedup(baseline: float, optimized: float) -> float:
    if optimized <= 0:
        return float("inf")
    return baseline / optimized


def print_row(name: str, time_s: float, speedup: float | None = None) -> None:
    if speedup is None:
        print(f"{name:32} {time_s:10.4f} s")
    else:
        print(f"{name:32} {time_s:10.4f} s   speedup {speedup:6.2f}×")


# ---------------------------------------------------------------------------
# CPU-bound experiment (page_score)
# ---------------------------------------------------------------------------

def run_cpu_bound_experiment(n_books: int = 20_000, workers: int = 4) -> list[dict]:
    print("\n" + "=" * 70)
    print(f"CPU-bound experiment  (n={n_books}, workers={workers})")
    print("=" * 70)

    books = generate_books(n_books)
    pages = [b.pages for b in books]

    results: list[dict] = []

    t_seq = benchmark_repeated(calculate_scores_sequential, pages, repeats=3)
    print_row("Sequential (baseline)", t_seq, 1.0)
    results.append({
        "experiment": "cpu_bound",
        "method": "Sequential",
        "data_size": n_books,
        "workers": 1,
        "mean_time_s": round(t_seq, 6),
        "speedup": 1.0,
    })

    t_thr = benchmark_repeated(calculate_scores_threads, pages, workers=workers, repeats=3)
    su_thr = calculate_speedup(t_seq, t_thr)
    print_row("ThreadPoolExecutor", t_thr, su_thr)
    results.append({
        "experiment": "cpu_bound",
        "method": "ThreadPoolExecutor",
        "data_size": n_books,
        "workers": workers,
        "mean_time_s": round(t_thr, 6),
        "speedup": round(su_thr, 3),
    })

    t_proc = benchmark_repeated(
        calculate_scores_processes, pages, workers=workers, repeats=3
    )
    su_proc = calculate_speedup(t_seq, t_proc)
    print_row("ProcessPoolExecutor", t_proc, su_proc)
    results.append({
        "experiment": "cpu_bound",
        "method": "ProcessPoolExecutor",
        "data_size": n_books,
        "workers": workers,
        "mean_time_s": round(t_proc, 6),
        "speedup": round(su_proc, 3),
    })

    return results


# ---------------------------------------------------------------------------
# Statistics experiment (Python vs NumPy)
# ---------------------------------------------------------------------------

def run_statistics_experiment(n_books: int = 200_000) -> list[dict]:
    print("\n" + "=" * 70)
    print(f"Statistics experiment  (n={n_books})")
    print("=" * 70)

    books = generate_books(n_books)
    pages = [b.pages for b in books]

    results: list[dict] = []

    t_py = benchmark_repeated(statistics_python, pages, repeats=5)
    print_row("Python statistics", t_py, 1.0)
    results.append({
        "experiment": "statistics",
        "method": "Python",
        "data_size": n_books,
        "workers": 1,
        "mean_time_s": round(t_py, 6),
        "speedup": 1.0,
    })

    t_np = benchmark_repeated(statistics_numpy, pages, repeats=5)
    su = calculate_speedup(t_py, t_np)
    print_row("NumPy statistics", t_np, su)
    results.append({
        "experiment": "statistics",
        "method": "NumPy",
        "data_size": n_books,
        "workers": "-",
        "mean_time_s": round(t_np, 6),
        "speedup": round(su, 3),
    })

    # Correctness check
    py_res = statistics_python(pages)
    np_res = statistics_numpy(pages)
    assert abs(py_res["average"] - np_res["average"]) < 1e-9
    print("  ✓ results match (tolerance 1e-9)")

    return results


# ---------------------------------------------------------------------------
# Author statistics experiment
# ---------------------------------------------------------------------------

def run_author_stats_experiment(n_books: int = 150_000) -> list[dict]:
    print("\n" + "=" * 70)
    print(f"Author statistics experiment  (n={n_books})")
    print("=" * 70)

    books = generate_books(n_books)
    results: list[dict] = []

    t_py = benchmark_repeated(author_statistics_python, books, repeats=3)
    print_row("Python author stats", t_py, 1.0)
    results.append({
        "experiment": "author_stats",
        "method": "Python",
        "data_size": n_books,
        "workers": 1,
        "mean_time_s": round(t_py, 6),
        "speedup": 1.0,
    })

    t_np = benchmark_repeated(author_statistics_numpy, books, repeats=3)
    su = calculate_speedup(t_py, t_np)
    print_row("NumPy author stats", t_np, su)
    results.append({
        "experiment": "author_stats",
        "method": "NumPy",
        "data_size": n_books,
        "workers": "-",
        "mean_time_s": round(t_np, 6),
        "speedup": round(su, 3),
    })

    return results


# ---------------------------------------------------------------------------
# Caching experiment
# ---------------------------------------------------------------------------

def run_caching_experiment(n_books: int = 100_000) -> list[dict]:
    print("\n" + "=" * 70)
    print(f"Caching experiment  (n={n_books})")
    print("=" * 70)

    books = generate_books(n_books)
    catalog = BookCatalog(books)
    author = books[0].author

    # Cold call
    start = perf_counter()
    _ = catalog.get_author_statistics_cached(author)
    cold = perf_counter() - start

    # Warm calls
    warm_times = []
    for _ in range(10):
        start = perf_counter()
        _ = catalog.get_author_statistics_cached(author)
        warm_times.append(perf_counter() - start)
    warm = mean(warm_times)

    print_row("Cold cache call", cold)
    print_row("Warm cache call (avg)", warm, calculate_speedup(cold, warm))

    # Invalidation demo
    catalog.add_book(Book("New Book", author, 2024, 300))
    start = perf_counter()
    _ = catalog.get_author_statistics_cached(author)
    after_inv = perf_counter() - start
    print_row("After invalidation (cold again)", after_inv)

    return [
        {
            "experiment": "caching",
            "method": "cold",
            "data_size": n_books,
            "workers": "-",
            "mean_time_s": round(cold, 6),
            "speedup": 1.0,
        },
        {
            "experiment": "caching",
            "method": "warm",
            "data_size": n_books,
            "workers": "-",
            "mean_time_s": round(warm, 6),
            "speedup": round(calculate_speedup(cold, warm), 3),
        },
    ]


# ---------------------------------------------------------------------------
# I/O-bound experiment (parallel file loading)
# ---------------------------------------------------------------------------

def prepare_io_files(n_files: int = 12, books_per_file: int = 5_000) -> list[Path]:
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    paths: list[Path] = []
    for i in range(n_files):
        path = data_dir / f"books_part_{i:02d}.json"
        if not path.exists():
            books = generate_books(books_per_file, seed=100 + i)
            # simple JSON-lines style for speed
            lines = [
                f'{{"title":"{b.title}","author":"{b.author}",'
                f'"year":{b.year},"pages":{b.pages}}}'
                for b in books
            ]
            path.write_text("\n".join(lines), encoding="utf-8")
        paths.append(path)
    return paths


def run_io_experiment() -> list[dict]:
    print("\n" + "=" * 70)
    print("I/O-bound experiment (parallel file loading)")
    print("=" * 70)

    paths = prepare_io_files()
    results: list[dict] = []

    t_seq = benchmark_repeated(load_files_sequential, paths, repeats=4)
    print_row("Sequential I/O", t_seq, 1.0)
    results.append({
        "experiment": "io_bound",
        "method": "Sequential",
        "data_size": len(paths),
        "workers": 1,
        "mean_time_s": round(t_seq, 6),
        "speedup": 1.0,
    })

    t_par = benchmark_repeated(load_files_parallel, paths, workers=8, repeats=4)
    su = calculate_speedup(t_seq, t_par)
    print_row("ThreadPoolExecutor I/O", t_par, su)
    results.append({
        "experiment": "io_bound",
        "method": "ThreadPoolExecutor",
        "data_size": len(paths),
        "workers": 8,
        "mean_time_s": round(t_par, 6),
        "speedup": round(su, 3),
    })

    return results


# ---------------------------------------------------------------------------
# Workers scaling experiment
# ---------------------------------------------------------------------------

def run_workers_scaling(n_books: int = 15_000) -> list[dict]:
    print("\n" + "=" * 70)
    print(f"Workers scaling experiment  (n={n_books})")
    print("=" * 70)

    books = generate_books(n_books)
    pages = [b.pages for b in books]
    results: list[dict] = []

    print(f"{'Workers':>8}  {'ThreadPool':>12}  {'ProcessPool':>12}")
    for w in [1, 2, 4, 8]:
        t_thr = benchmark_repeated(calculate_scores_threads, pages, workers=w, repeats=2)
        t_proc = benchmark_repeated(
            calculate_scores_processes, pages, workers=w, repeats=2
        )
        print(f"{w:8d}  {t_thr:12.4f}  {t_proc:12.4f}")
        results.append({
            "experiment": "workers_scaling",
            "method": "ThreadPoolExecutor",
            "data_size": n_books,
            "workers": w,
            "mean_time_s": round(t_thr, 6),
            "speedup": "",
        })
        results.append({
            "experiment": "workers_scaling",
            "method": "ProcessPoolExecutor",
            "data_size": n_books,
            "workers": w,
            "mean_time_s": round(t_proc, 6),
            "speedup": "",
        })

    return results


# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------

def save_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["experiment", "method", "data_size", "workers", "mean_time_s", "speedup"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nResults saved to {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Lab 09 — Book Catalog Benchmark Suite (Variant 2)")
    print(f"CPU count: {os.cpu_count()}")
    print(f"Python: {sys.version}")

    all_results: list[dict] = []

    all_results.extend(run_statistics_experiment(200_000))
    all_results.extend(run_author_stats_experiment(120_000))
    all_results.extend(run_cpu_bound_experiment(12_000, workers=4))
    all_results.extend(run_caching_experiment(80_000))
    all_results.extend(run_io_experiment())
    all_results.extend(run_workers_scaling(10_000))

    out = ROOT / "benchmarks" / "results" / "benchmark_results.csv"
    save_csv(all_results, out)

    print("\n" + "=" * 70)
    print("All experiments finished.")
    print("=" * 70)


if __name__ == "__main__":
    main()
