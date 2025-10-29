from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .repository.state import ClassificationReport


@dataclass
class AggregatedMetrics:
    """Интегральные показатели качества производственной системы."""

    average_health: float
    anomaly_ratio: float
    critical_probability: float


def summarize_reports(reports: Iterable[ClassificationReport]) -> AggregatedMetrics:
    total = 0
    health_sum = 0.0
    anomaly_count = 0
    anomaly_total = 0
    probability_sum = 0.0

    for report in reports:
        total += 1
        health_sum += report.health_index
        probability_sum += report.probability
        for score in report.anomalies.values():
            anomaly_total += 1
            if score >= 3.0:
                anomaly_count += 1

    if total == 0:
        return AggregatedMetrics(average_health=1.0, anomaly_ratio=0.0, critical_probability=0.0)

    average_health = health_sum / total
    anomaly_ratio = anomaly_count / anomaly_total if anomaly_total else 0.0
    critical_probability = probability_sum / total
    return AggregatedMetrics(
        average_health=average_health,
        anomaly_ratio=anomaly_ratio,
        critical_probability=critical_probability,
    )
