"""Обнаружение аномалий на основе порогов и трендов."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .config import AnomalyConfig
from .preprocessing import NormalizedEvent


@dataclass
class AnomalyResult:
    """Результат проверки на аномалии."""

    is_anomaly: bool
    reasons: List[str]
    score: float


class AnomalyDetector:
    """Простой детектор, комбинирующий пороговые проверки и тренды."""

    def __init__(self, config: AnomalyConfig) -> None:
        self.config = config

    def evaluate(self, event: NormalizedEvent) -> AnomalyResult:
        reasons: list[str] = []
        score = 0.0
        source = event.source

        if source.temperature >= self.config.temperature_limit:
            reasons.append("превышена температура")
            score += 0.5

        if source.vibration >= self.config.vibration_limit:
            reasons.append("повышена вибрация")
            score += 0.3

        if source.pressure >= self.config.pressure_limit:
            reasons.append("увеличилось давление")
            score += 0.2

        # Анализ тренда: растущая дисперсия может указывать на разбалансировку
        _, t_std, _, v_std, _, p_std = event.rolling_vector
        trend_score = sum([t_std, v_std, p_std]) / max(1.0, self.config.window)
        score += trend_score * self.config.sensitivity

        return AnomalyResult(is_anomaly=bool(reasons or score > 0.7), reasons=reasons, score=score)
