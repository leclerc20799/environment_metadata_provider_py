"""Environment Metadata Provider.

Collects hostname, process ID, Python version, and boot time once at startup,
exposing them as a frozen dict for log record enrichment.
"""

from .core import collect_environment_metadata

__all__ = ["collect_environment_metadata"]
