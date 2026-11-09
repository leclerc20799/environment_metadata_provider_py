# environment_metadata_provider_py

Collects hostname, process ID, Python version, and boot time once at startup,
exposing them as a frozen dict for log record enrichment.

## Usage

```python
from environment_metadata_provider_py import collect_environment_metadata

metadata = collect_environment_metadata()
print(metadata["hostname"])
print(metadata["pid"])
print(metadata["python_version"])
print(metadata["boot_time"])
```

The returned object is a `MappingProxyType`, so it is read-only. Log formatters
can safely read from a shared metadata object without any chance of mutating it.

## Why this exists

Log records often need to carry stable process-level context. Recomputing that
context on every log call is wasteful, and recomputing it lazily can produce
inconsistent records if the process environment changes (for example, after a
fork). This library captures the values exactly once and freezes them.

The trade-off: if the process forks, the child inherits the parent's metadata,
including the parent's PID. Callers that care about fork safety should call
`collect_environment_metadata` again in the child and replace their reference.

## Edge case: boot time on non-Linux systems

`boot_time` is read from the `btime` line in `/proc/stat`. On systems without
that file (macOS, Windows, some containers), `collect_environment_metadata`
raises `RuntimeError` at startup rather than returning a misleading value. This
is intentional: a log enricher that silently reports the wrong boot time is
worse than one that fails loudly. If you need portable boot-time detection, wrap
the call and provide your own fallback.
