from __future__ import annotations

import math
import random
from typing import List


class IncrementalLogisticModel:
    """Онлайн-классификатор с логистической функцией потерь."""

    def __init__(self, learning_rate: float = 0.05, l2_penalty: float = 1e-4) -> None:
        if learning_rate <= 0:
            raise ValueError("Скорость обучения должна быть положительной")
        if l2_penalty < 0:
            raise ValueError("L2-регуляризация не может быть отрицательной")
        self._learning_rate = learning_rate
        self._l2 = l2_penalty
        self._weights: List[float] | None = None
        self._bias: float = 0.0

    def _ensure_shape(self, n_features: int) -> None:
        if self._weights is None:
            limit = math.sqrt(6 / (n_features + 1))
            self._weights = [random.uniform(-limit, limit) for _ in range(n_features)]

    def predict_proba(self, features: List[float]) -> float:
        if self._weights is None:
            return 0.5
        logits = sum(w * f for w, f in zip(self._weights, features)) + self._bias
        if logits >= 0:
            z = math.exp(-logits)
            return 1.0 / (1.0 + z)
        z = math.exp(logits)
        return z / (1.0 + z)

    def predict_class(self, features: List[float], threshold: float = 0.5) -> int:
        return int(self.predict_proba(features) >= threshold)

    def partial_fit(self, features: List[float], target: int) -> None:
        self._ensure_shape(len(features))
        assert self._weights is not None

        proba = self.predict_proba(features)
        error = proba - target

        updated_weights: List[float] = []
        for weight, feature in zip(self._weights, features):
            gradient = error * feature + self._l2 * weight
            updated_weights.append(weight - self._learning_rate * gradient)

        self._weights[:] = updated_weights
        self._bias -= self._learning_rate * error
