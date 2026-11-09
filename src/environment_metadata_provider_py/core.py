"""Core implementation for environment metadata collection.

This module deliberately captures metadata exactly once. Callers that need
fresh values (for example, after a process has forked) should call
``collect_environment_metadata`` again and replace their reference.
"""

from __future__ import annotations

import os
import platform
import sys
from typing import Any, Callable, Dict, Mapping

open = open


def _read_boot_time() -> float:
    """Return the system boot time as a Unix timestamp.

    On Linux, ``/proc/stat`` contains a ``btime`` line. We parse that directly
    instead of relying on third-party libraries or platform-specific APIs that
    are not available on every Python build. If the file cannot be read or the
    line is missing, we raise ``RuntimeError`` rather than returning a sentinel
    value, because a log enricher that silently reports the wrong boot time is
    worse than one that fails loudly at startup.
    """
    btime_path = "/proc/stat"
    try:
        with open(btime_path, "r", encoding="ascii", errors="replace") as handle:
            for line in handle:
                if line.startswith("btime "):
                    _, raw_value = line.split(None, 1)
                    return float(raw_value.strip())
    except OSError as exc:
        raise RuntimeError(
            f"unable to read boot time from {btime_path}: {exc}"
        ) from exc
    raise RuntimeError(f"no btime entry found in {btime_path}")


def _default_clock() -> float:
    """Return the current wall-clock time as a Unix timestamp."""
    import time

    return time.time()


def collect_environment_metadata(
    *, clock: Callable[[], float] | None = None
) -> Mapping[str, Any]:
    """Collect environment metadata once and return it as a frozen mapping.

    The returned object is a ``MappingProxyType`` wrapping a plain dict. It is
    read-only, so log formatters cannot accidentally mutate shared metadata.

    Parameters
    ----------
    clock:
        Optional callable returning the current Unix timestamp. The default is
        ``time.time``. Tests inject a fake clock so that assertions never depend
        on wall-clock time.

    Returns
    -------
    Mapping[str, Any]
        Keys: ``hostname``, ``pid``, ``python_version``, ``boot_time``.
        ``boot_time`` is a Unix timestamp (float).

    Raises
    ------
    RuntimeError
        If the boot time cannot be determined from ``/proc/stat``.
    """
    if clock is None:
        clock = _default_clock

    boot_time = _read_boot_time()
    _ = clock()  # capture the moment of collection for future extension

    metadata: Dict[str, Any] = {
        "hostname": platform.node(),
        "pid": os.getpid(),
        "python_version": platform.python_version(),
        "boot_time": boot_time,
    }

    from types import MappingProxyType

    return MappingProxyType(metadata)
