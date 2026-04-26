import functools
import logging
import sys
import time
import tracemalloc
from typing import Any, Dict

from src.app.logger import get_logger

logger = get_logger(
    __name__,
    log_file="logs/profile_log.log",
    file_level=logging.DEBUG,
)

try:
    import resource

    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

import psutil


class ProfileBlock:
    def __init__(self, name: str = "", track_tracemalloc: bool = True):
        self.name = name
        self.track_tracemalloc = track_tracemalloc
        self.elapsed: float = 0.0
        self.peak_rss_kb: int = 0
        self.peak_traced_kb: int = 0

    def __enter__(self):
        if HAS_RESOURCE:
            self._start_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        else:
            self._start_rss = 0

        if self.track_tracemalloc:
            tracemalloc.start()

        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start_time

        if HAS_RESOURCE:
            end_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self.peak_rss_kb = max(0, end_rss - self._start_rss)
            if sys.platform == "darwin":
                self.peak_rss_kb //= 1024
        else:
            end_rss = psutil.Process().memory_info().rss // 1024
            self.peak_rss_kb = max(0, end_rss - self._start_rss)

        if self.track_tracemalloc:
            _, traced_peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            self.peak_traced_kb = traced_peak // 1024

        logger.debug(
            f"[ProfileBlock] Результаты профилирования: {self.name}, \ndict:{self.as_dict()}"
        )
        return False

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "elapsed_sec": round(self.elapsed, 4),
            "peak_rss_kb": self.peak_rss_kb,
            "peak_rss_mb": round(self.peak_rss_kb / 1024, 3) if self.peak_rss_kb else 0,
            "peak_traced_kb": self.peak_traced_kb,
            "peak_traced_mb": round(self.peak_traced_kb / 1024, 3),
        }

    def __str__(self):
        d = self.as_dict()
        rss_part = f"пик RSS={d['peak_rss_mb']}МБ, " if d["peak_rss_mb"] else ""
        return (
            f"[{d['name']}] время={d['elapsed_sec']}с, "
            f"{rss_part}"
            f"пик Python-кучи={d['peak_traced_mb']}МБ"
        )
