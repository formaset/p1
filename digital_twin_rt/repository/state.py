from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional


@dataclass
class ClassificationReport:
    probability: float
    predicted_class: int
    anomalies: Dict[str, float]
    health_index: float


class StateRepository:
    """Хранилище агрегированных метрик по последним наблюдениям."""

    def __init__(self, max_records: int = 1000) -> None:
        if max_records <= 0:
            raise ValueError("Размер хранилища должен быть положительным")
        self._states: Deque[ClassificationReport] = deque(maxlen=max_records)

    def push(self, report: ClassificationReport) -> None:
        self._states.append(report)

    def last(self) -> Optional[ClassificationReport]:
        return self._states[-1] if self._states else None

    def __len__(self) -> int:
        return len(self._states)

    def __iter__(self):
        return iter(self._states)

    def health_score(self) -> float:
        if not self._states:
            return 1.0
        return sum(state.health_index for state in self._states) / len(self._states)

    def anomaly_rate(self, threshold: float = 3.0) -> float:
        if not self._states:
            return 0.0
        count = 0
        total = 0
        for state in self._states:
            for score in state.anomalies.values():
                total += 1
                if score >= threshold:
                    count += 1
        return count / total if total else 0.0
