# Book Manager — Lab 09 (Варіант 2)

**Паралельність, багатопроцесність та оптимізація**  
Система обліку книг (продовження Lab 01).

## Опис

Проєкт реалізує експериментальне профілювання та оптимізацію каталогу книг:

- Baseline (чисті Python-цикли)
- ThreadPoolExecutor (I/O-bound)
- ProcessPoolExecutor (CPU-bound)
- NumPy vectorization
- Caching (`lru_cache`) + cache invalidation
- Synchronization (`Lock`) + демонстрація race condition
- cProfile + tracemalloc
- Повний набір бенчмарків зі speedup

## Структура

```
book_manager/
├── pyproject.toml
├── README.md
├── src/book_manager/
│   ├── __init__.py
│   ├── models.py          # Book dataclass
│   ├── analytics.py       # генерація даних, baseline, NumPy, caching
│   ├── parallel.py        # threading, ProcessPool, ThreadPool, Lock
│   ├── services.py        # BookCatalog + invalidation
│   ├── profiling.py       # cProfile + tracemalloc
│   └── main.py            # швидке демо
├── tests/
│   ├── test_analytics.py
│   ├── test_parallel.py
│   └── test_services.py
├── benchmarks/
│   ├── benchmark.py       # головний експериментальний скрипт
│   └── results/
│       └── benchmark_results.csv
└── data/                  # згенеровані JSON-файли для I/O-експерименту
```

## Встановлення

```bash
cd book_manager
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Запуск

### Швидке демо
```bash
python -m book_manager.main
```

### Профілювання
```bash
python -m book_manager.profiling
```

### Повний бенчмарк (рекомендовано)
```bash
python benchmarks/benchmark.py
```

Результати зберігаються в `benchmarks/results/benchmark_results.csv`.

### Тести
```bash
pytest -v
```

## Експерименти, що виконуються

| Експеримент              | Що порівнюється                          | Очікуваний висновок                          |
|--------------------------|------------------------------------------|----------------------------------------------|
| Statistics               | Python loops vs NumPy                    | NumPy значно швидший                         |
| Author statistics        | Python vs NumPy                          | NumPy виграє на агрегатах                    |
| CPU-bound (page_score)   | Sequential / ThreadPool / ProcessPool    | ProcessPool прискорює, ThreadPool — ні (GIL) |
| Workers scaling          | 1 / 2 / 4 / 8 workers                    | ProcessPool масштабується, ThreadPool — ні   |
| Caching                  | Cold vs Warm + invalidation              | Warm cache ≈ миттєвий                        |
| I/O-bound                | Sequential read vs ThreadPoolExecutor    | Threading дає прискорення на I/O             |

## Приклад таблиці результатів

(цифри залежать від машини)

| Method                 | Mean time, s | Speedup |
|------------------------|--------------|---------|
| Python statistics      | 0.185        | 1.00×   |
| NumPy statistics       | 0.009        | 20.5×   |
| Sequential (CPU)       | 3.12         | 1.00×   |
| ThreadPoolExecutor     | 3.45         | 0.90×   |
| ProcessPoolExecutor    | 1.05         | 2.97×   |
| Cold cache             | 0.012        | 1.00×   |
| Warm cache             | 0.00002      | ~600×   |

## Ключові висновки (типові)

1. **GIL** — ThreadPoolExecutor майже не прискорює CPU-bound Python-код.
2. **ProcessPoolExecutor** дає реальний parallelism і прискорення на багатоядерних CPU.
3. **NumPy** часто є найефективнішим способом для числової статистики (векторизація).
4. **Caching** має сенс тільки при повторних запитах; після зміни даних потрібна **invalidation**.
5. Для I/O-bound задач (читання багатьох файлів) ThreadPoolExecutor працює добре.

## Вимоги методички (виконано)

- [x] Baseline implementation  
- [x] Достатній обсяг даних (100k–200k книг)  
- [x] CPU-bound + I/O-bound операції  
- [x] timeit / perf_counter  
- [x] cProfile  
- [x] tracemalloc  
- [x] Bottleneck detection  
- [x] threading + ThreadPoolExecutor  
- [x] multiprocessing + ProcessPoolExecutor  
- [x] Synchronization (Lock) + race condition demo  
- [x] NumPy  
- [x] Caching + invalidation  
- [x] Порівняння ≥ 3 реалізацій  
- [x] Повторні бенчмарки + speedup  
- [x] Перевірка правильності результатів  
- [x] Таблиця експериментальних результатів (CSV)

## Автор

Лабораторна робота №9, варіант 2  
2026
