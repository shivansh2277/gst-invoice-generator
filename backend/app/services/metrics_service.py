"""In-memory app metrics."""

from collections import Counter

metrics_counter: Counter[str] = Counter()


def inc(metric: str) -> None:
    metrics_counter[metric] += 1


def render_prometheus() -> str:
    lines = [f"{key} {value}" for key, value in sorted(metrics_counter.items())]
    return "\n".join(lines) + "\n"
