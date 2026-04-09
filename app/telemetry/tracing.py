from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


@contextmanager
def trace_span(_name: str) -> Iterator[None]:
    yield
