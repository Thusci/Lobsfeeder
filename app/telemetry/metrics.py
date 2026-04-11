from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Mapping


def _labels_key(labels: Mapping[str, str] | None) -> tuple[tuple[str, str], ...]:
    if not labels:
        return tuple()
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


class MetricsRegistry:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._lock = Lock()
        self._counters: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(dict)
        self._histograms: dict[str, dict[tuple[tuple[str, str], ...], list[float]]] = defaultdict(dict)
        self._gauges: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(dict)

    def inc(self, name: str, labels: Mapping[str, str] | None = None, value: float = 1.0) -> None:
        if not self.enabled:
            return
        key = _labels_key(labels)
        with self._lock:
            self._counters[name][key] = self._counters[name].get(key, 0.0) + value

    def observe(self, name: str, value: float, labels: Mapping[str, str] | None = None) -> None:
        if not self.enabled:
            return
        key = _labels_key(labels)
        with self._lock:
            self._histograms[name].setdefault(key, []).append(value)

    def set_gauge(self, name: str, value: float, labels: Mapping[str, str] | None = None) -> None:
        if not self.enabled:
            return
        key = _labels_key(labels)
        with self._lock:
            self._gauges[name][key] = value

    def render_prometheus(self) -> str:
        if not self.enabled:
            return ""

        lines: list[str] = []
        with self._lock:
            for metric_name, series in self._counters.items():
                lines.append(f"# TYPE {metric_name} counter")
                for labels, value in series.items():
                    if labels:
                        label_str = ",".join(f'{k}="{v}"' for k, v in labels)
                        lines.append(f"{metric_name}{{{label_str}}} {value}")
                    else:
                        lines.append(f"{metric_name} {value}")

            for metric_name, series in self._histograms.items():
                lines.append(f"# TYPE {metric_name} summary")
                for labels, values in series.items():
                    if not values:
                        continue
                    avg = sum(values) / len(values)
                    if labels:
                        label_str = ",".join(f'{k}="{v}"' for k, v in labels)
                        lines.append(f"{metric_name}_count{{{label_str}}} {len(values)}")
                        lines.append(f"{metric_name}_avg{{{label_str}}} {avg}")
                    else:
                        lines.append(f"{metric_name}_count {len(values)}")
                        lines.append(f"{metric_name}_avg {avg}")

            for metric_name, series in self._gauges.items():
                lines.append(f"# TYPE {metric_name} gauge")
                for labels, value in series.items():
                    if labels:
                        label_str = ",".join(f'{k}="{v}"' for k, v in labels)
                        lines.append(f"{metric_name}{{{label_str}}} {value}")
                    else:
                        lines.append(f"{metric_name} {value}")

        return "\n".join(lines) + "\n"
