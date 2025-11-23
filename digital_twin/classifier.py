"""Классификатор состояния агрегата."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .config import ClassifierConfig
from .anomaly import AnomalyResult
from .preprocessing import NormalizedEvent


@dataclass
class Classification:
    """Результат работы классификатора."""

    label: str
    probability: float
    rationale: List[str]


class WeightedClassifier:
    """Нечёткий классификатор, суммирующий метрики по весам."""

    def __init__(self, config: ClassifierConfig) -> None:
        self.config = config

    def classify(self, event: NormalizedEvent, anomaly: AnomalyResult) -> Classification:
        # Взвешиваем нормализованные показатели для вычисления общей опасности
        weighted_score = (
            event.normalized_temperature * self.config.weight_temperature
            + event.normalized_vibration * self.config.weight_vibration
            + event.normalized_pressure * self.config.weight_pressure
        )
        weighted_score = min(1.0, max(0.0, weighted_score + anomaly.score))
        label_index = 0
        rationale: list[str] = []

        if weighted_score > 0.7:
            label_index = 2
            rationale.append("высокий риск")
        elif weighted_score > 0.4:
            label_index = 1
            rationale.append("средний риск")
        else:
            rationale.append("стабильное состояние")

        if anomaly.reasons:
            rationale.extend(anomaly.reasons)

        probability = weighted_score if label_index > 0 else 1.0 - weighted_score
        return Classification(label=self.config.classes[label_index], probability=probability, rationale=rationale)
