"""Набор шагов предобработки данных."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Deque, Iterable, List

from .telemetry import TelemetryEvent


@dataclass
class NormalizedEvent:
    """Событие после нормализации и обогащения."""

    source: TelemetryEvent
    normalized_temperature: float
    normalized_vibration: float
    normalized_pressure: float
    rolling_vector: List[float]


class RollingStatistics:
    """Поддержание скользящих метрик для оценки трендов."""

    def __init__(self, window: int) -> None:
        self.window = window
        self._temperatures: Deque[float] = deque(maxlen=window)
        self._vibrations: Deque[float] = deque(maxlen=window)
        self._pressures: Deque[float] = deque(maxlen=window)

    def update(self, event: TelemetryEvent) -> None:
        self._temperatures.append(event.temperature)
        self._vibrations.append(event.vibration)
        self._pressures.append(event.pressure)

    def snapshot(self) -> dict[str, float]:
        """Возвращает текущие агрегаты по окну."""
        return {
            "t_avg": mean(self._temperatures) if self._temperatures else 0.0,
            "t_std": pstdev(self._temperatures) if len(self._temperatures) > 1 else 0.0,
            "v_avg": mean(self._vibrations) if self._vibrations else 0.0,
            "v_std": pstdev(self._vibrations) if len(self._vibrations) > 1 else 0.0,
            "p_avg": mean(self._pressures) if self._pressures else 0.0,
            "p_std": pstdev(self._pressures) if len(self._pressures) > 1 else 0.0,
        }


class PreprocessingPipeline:
    """Сквозная предобработка: фильтрация, нормализация, агрегация."""

    def __init__(self, window: int = 30) -> None:
        self.stats = RollingStatistics(window=window)

    def _normalize(self, value: float, baseline: float, scale: float) -> float:
        # Простая линейная нормализация в диапазон [0, 1]
        return max(0.0, min(1.0, (value - baseline) / scale))

    def process(self, event: TelemetryEvent) -> NormalizedEvent:
        """Основной метод предобработки."""
        self.stats.update(event)
        snapshot = self.stats.snapshot()
        normalized_temperature = self._normalize(event.temperature, baseline=50, scale=50)
        normalized_vibration = self._normalize(event.vibration, baseline=0, scale=10)
        normalized_pressure = self._normalize(event.pressure, baseline=8, scale=12)
        rolling_vector = [
            snapshot["t_avg"],
            snapshot["t_std"],
            snapshot["v_avg"],
            snapshot["v_std"],
            snapshot["p_avg"],
            snapshot["p_std"],
        ]
        return NormalizedEvent(
            source=event,
            normalized_temperature=normalized_temperature,
            normalized_vibration=normalized_vibration,
            normalized_pressure=normalized_pressure,
            rolling_vector=rolling_vector,
        )

    def bulk_process(self, events: Iterable[TelemetryEvent]) -> Iterable[NormalizedEvent]:
        """Пакетная обработка коллекции событий."""
        for event in events:
            yield self.process(event)
