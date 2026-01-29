"""Prometheus metrics for Atlas API.

Lightweight metrics collection without requiring prometheus_client.
Exposes /metrics endpoint in Prometheus text exposition format.
"""

import threading
from collections import defaultdict


class MetricsCollector:
    """Thread-safe metrics collector exposing Prometheus text format."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}

    def inc_counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._counters[key] += 1

    def observe_histogram(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._histograms[key].append(value)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def _key(self, name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def render(self) -> str:
        """Render metrics in Prometheus text exposition format."""
        lines: list[str] = []
        with self._lock:
            for key, val in sorted(self._counters.items()):
                lines.append(f"{key} {val}")
            for key, val in sorted(self._gauges.items()):
                lines.append(f"{key} {val}")
            for key, values in sorted(self._histograms.items()):
                if values:
                    base = key.split("{")[0] if "{" in key else key
                    labels = key[len(base):] if "{" in key else ""
                    count = len(values)
                    total = sum(values)
                    lines.append(f"{base}_count{labels} {count}")
                    lines.append(f"{base}_sum{labels} {total:.4f}")
        lines.append("")
        return "\n".join(lines)


# Singleton
_collector = MetricsCollector()


def get_metrics() -> MetricsCollector:
    return _collector
