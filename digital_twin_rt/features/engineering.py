from __future__ import annotations

import math
from collections import deque
from typing import Deque, Dict, List


class FeatureEngineer:
    """Формирует расширенное описание состояния процесса."""

    def __init__(self, window: int = 8) -> None:
        if window <= 1:
            raise ValueError("Размер окна должен быть больше 1")
        self._window = window
        self._history: Dict[str, Deque[float]] = {}
        self._previous: Dict[str, float] = {}

    def transform(self, values: Dict[str, float]) -> List[float]:
        features: List[float] = []
        for name in sorted(values):
            value = values[name]
            history = self._history.setdefault(name, deque(maxlen=self._window))
            history.append(value)

            avg = sum(history) / len(history)
            variance = sum((v - avg) ** 2 for v in history) / max(len(history) - 1, 1)
            std = math.sqrt(variance)
            prev = self._previous.get(name, value)
            gradient = value - prev
            self._previous[name] = value

            features.extend([value, avg, std, gradient])
        return features
