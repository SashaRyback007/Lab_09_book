"""Threading, multiprocessing and concurrent.futures helpers."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from threading import Lock, Thread
from typing import Callable

from book_manager.analytics import page_score


# ---------------------------------------------------------------------------
# Threading examples
# ---------------------------------------------------------------------------

def process_item(item_id: int) -> None:
    print(f"Processing {item_id}")


def run_simple_threads(n: int = 5) -> None:
    threads: list[Thread] = []
    for item_id in range(n):
        t = Thread(target=process_item, args=(item_id,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


# ---------------------------------------------------------------------------
# Race condition demo + Lock
# ---------------------------------------------------------------------------

_counter = 0
_counter_lock = Lock()


def reset_counter() -> None:
    global _counter
    _counter = 0


def get_counter() -> int:
    return _counter


def increment_unsafe() -> None:
    """Intentionally racy — for demonstration only."""
    global _counter
    current = _counter
    # artificial delay window for race
    _counter = current + 1


def increment_safe() -> None:
    global _counter
    with _counter_lock:
        _counter += 1


def run_race_demo(workers: int = 8, iterations: int = 10_000) -> tuple[int, int]:
    """
    Returns (unsafe_result, safe_result).
    unsafe_result is often < expected because of race conditions.
    """
    # Unsafe
    reset_counter()
    threads = [
        Thread(target=lambda: [increment_unsafe() for _ in range(iterations)])
        for _ in range(workers)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    unsafe = get_counter()

    # Safe
    reset_counter()
    threads = [
        Thread(target=lambda: [increment_safe() for _ in range(iterations)])
        for _ in range(workers)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    safe = get_counter()
    return unsafe, safe


# ---------------------------------------------------------------------------
# ThreadPoolExecutor — good for I/O-bound
# ---------------------------------------------------------------------------

def calculate_scores_threads(
    pages_list: list[int],
    workers: int = 4,
) -> list[float]:
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(page_score, pages_list))


def load_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_files_parallel(paths: list[Path], workers: int = 8) -> list[str]:
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(load_file, paths))


def load_files_sequential(paths: list[Path]) -> list[str]:
    return [load_file(p) for p in paths]


# ---------------------------------------------------------------------------
# ProcessPoolExecutor — good for CPU-bound
# ---------------------------------------------------------------------------

def calculate_scores_processes(
    pages_list: list[int],
    workers: int = 4,
    chunksize: int = 100,
) -> list[float]:
    # Must be top-level / picklable for multiprocessing
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(
            executor.map(page_score, pages_list, chunksize=chunksize)
        )


# ---------------------------------------------------------------------------
# Generic helpers used by benchmarks
# ---------------------------------------------------------------------------

def map_parallel(
    func: Callable,
    items: list,
    *,
    use_processes: bool = False,
    workers: int = 4,
    chunksize: int = 100,
) -> list:
    if use_processes:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(func, items, chunksize=chunksize))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(func, items))
