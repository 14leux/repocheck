#!/usr/bin/env python3
"""
RepoCheck -- shared concurrency helper (OI-019).

verdict.py's full pipeline took ~6 minutes on a real 390-file repo,
entirely from sequential, uncached network calls (GitHub contents API
per file, OSV.dev per vulnerability, npm/PyPI per dependency). None of
these calls depend on each other, so they're a natural fit for a thread
pool -- this is I/O-bound waiting, not CPU work, so threads (not
asyncio, not multiprocessing) are the right tool and need no new
dependency.

Deliberately simple: one function, no retry/backoff logic (a genuinely
separate concern), a bounded worker count to stay well under GitHub's
and OSV.dev's rate limits rather than firing everything at once.
"""

from concurrent.futures import ThreadPoolExecutor

DEFAULT_MAX_WORKERS = 10


def parallel_map(fn, items, max_workers=DEFAULT_MAX_WORKERS):
    """
    Runs fn(item) for each item concurrently. Returns a list of results
    in the SAME ORDER as items (not completion order), so callers can
    zip() it against the original items list exactly as they did with
    the old sequential loop.

    A failing item's exception is returned as the result value itself,
    not raised -- one bad fetch must not abort the whole batch. Callers
    check `isinstance(result, Exception)`.
    """
    if not items:
        return []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fn, item) for item in items]
        results = []
        for f in futures:
            try:
                results.append(f.result())
            except Exception as e:
                results.append(e)
        return results
