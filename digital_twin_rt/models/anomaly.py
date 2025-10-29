from __future__ import annotations

import math
from typing import Dict


class AnomalyDetector:
    """Онлайн-оценка статистических отклонений сенсоров."""

    def __init__(self) -> None:
        self._count: Dict[str, int] = {}
        self._mean: Dict[str, float] = {}
        self._m2: Dict[str, float] = {}

    def register(self, values: Dict[str, float]) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for name, value in values.items():
            count = self._count.get(name, 0)
            mean = self._mean.get(name, 0.0)
            m2 = self._m2.get(name, 0.0)

            count += 1
            delta = value - mean
            mean += delta / count
            delta2 = value - mean
            m2 += delta * delta2

            self._count[name] = count
            self._mean[name] = mean
            self._m2[name] = m2

            variance = m2 / (count - 1) if count > 1 else 0.0
            std = math.sqrt(variance)
            if std > 0:
                scores[name] = abs(value - mean) / std
            else:
                scores[name] = 0.0
        return scores
