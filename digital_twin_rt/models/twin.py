from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..config import SensorSpecification


@dataclass
class DigitalTwinAssessment:
    """Диагностический отчёт цифрового двойника."""

    predicted: Dict[str, float]
    deviation: Dict[str, float]
    health_index: float


class DigitalTwinModel:
    """Сопоставляет ожидаемое и фактическое состояние производственной системы."""

    def __init__(self, reference: Dict[str, SensorSpecification]) -> None:
        if not reference:
            raise ValueError("Базовая модель цифрового двойника не может быть пустой")
        self._reference = reference
        self._drift: Dict[str, float] = {name: 0.0 for name in reference}

    def evaluate(self, values: Dict[str, float]) -> DigitalTwinAssessment:
        predicted: Dict[str, float] = {}
        deviation: Dict[str, float] = {}
        penalties: list[float] = []

        for name, spec in self._reference.items():
            actual = values.get(name, spec.nominal)
            drift = self._drift[name]
            predicted_value = spec.nominal + drift
            error = actual - predicted_value
            deviation[name] = error
            predicted[name] = predicted_value

            # Простая адаптация параметров цифрового двойника к наблюдаемым отклонениям.
            self._drift[name] += 0.01 * error

            normalized = abs(error) / (spec.spread or 1.0)
            penalties.append(min(normalized, 5.0))

        health_index = max(0.0, 1.0 - sum(penalties) / (len(penalties) * 5.0))
        return DigitalTwinAssessment(predicted=predicted, deviation=deviation, health_index=health_index)
