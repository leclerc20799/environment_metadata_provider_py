import os
import platform
import unittest
from types import MappingProxyType

from environment_metadata_provider_py import collect_environment_metadata


class TestCollectEnvironmentMetadata(unittest.TestCase):
    def test_returns_frozen_mapping(self):
        metadata = collect_environment_metadata(clock=lambda: 0.0)
        self.assertIsInstance(metadata, MappingProxyType)
        with self.assertRaises(TypeError):
            metadata["hostname"] = "other"  # type: ignore[index]

    def test_contains_expected_keys(self):
        metadata = collect_environment_metadata(clock=lambda: 0.0)
        self.assertEqual(
            set(metadata.keys()),
            {"hostname", "pid", "python_version", "boot_time"},
        )

    def test_values_match_stdlib_sources(self):
        metadata = collect_environment_metadata(clock=lambda: 0.0)
        self.assertEqual(metadata["hostname"], platform.node())
        self.assertEqual(metadata["pid"], os.getpid())
        self.assertEqual(metadata["python_version"], platform.python_version())
        self.assertIsInstance(metadata["boot_time"], float)

    def test_boot_time_is_positive(self):
        metadata = collect_environment_metadata(clock=lambda: 0.0)
        self.assertGreater(metadata["boot_time"], 0.0)

    def test_clock_is_invoked_once(self):
        calls = []

        def fake_clock() -> float:
            calls.append(1)
            return 123.0

        collect_environment_metadata(clock=fake_clock)
        self.assertEqual(len(calls), 1)

    def test_missing_proc_stat_raises_runtime_error(self):
        import environment_metadata_provider_py.core as core

        original_open = core.open

        def failing_open(*args, **kwargs):
            raise FileNotFoundError("no /proc/stat here")

        core.open = failing_open  # type: ignore[assignment]
        try:
            with self.assertRaises(RuntimeError) as ctx:
                collect_environment_metadata(clock=lambda: 0.0)
            self.assertIn("unable to read boot time", str(ctx.exception))
        finally:
            core.open = original_open  # type: ignore[assignment]

    def test_proc_stat_without_btime_raises_runtime_error(self):
        import environment_metadata_provider_py.core as core

        original_open = core.open

        class FakeHandle:
            def __init__(self, lines):
                self._lines = iter(lines)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def __iter__(self):
                return self

            def __next__(self):
                return next(self._lines)

        def fake_open(path, *args, **kwargs):
            return FakeHandle(["cpu 1 2 3\n", "intr 0\n"])

        core.open = fake_open  # type: ignore[assignment]
        try:
            with self.assertRaises(RuntimeError) as ctx:
                collect_environment_metadata(clock=lambda: 0.0)
            self.assertIn("no btime entry", str(ctx.exception))
        finally:
            core.open = original_open  # type: ignore[assignment]


if __name__ == "__main__":
    unittest.main()
