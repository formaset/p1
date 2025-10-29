from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass
from typing import Dict, Mapping, MutableMapping, Tuple


@dataclass(frozen=True)
class SensorSpecification:
    """Параметры виртуального сенсора цифрового двойника."""

    nominal: float
    spread: float

    def validate(self, name: str) -> None:
        if self.spread <= 0:
            raise ValueError(f"Для сенсора '{name}' разброс должен быть положительным")


@dataclass
class StreamConfig:
    """Конфигурация генерации и искажения данных."""

    sensors: MutableMapping[str, SensorSpecification]
    anomaly_probability: float = 0.05
    delay_seconds: float = 0.05
    noise_level: float = 0.03
    seed: int | None = None

    def __post_init__(self) -> None:
        if not self.sensors:
            raise ValueError("Список сенсоров не может быть пустым")
        for name, spec in self.sensors.items():
            spec.validate(name)
        if not (0.0 <= self.anomaly_probability <= 1.0):
            raise ValueError("Вероятность аномалии должна находиться в диапазоне [0, 1]")
        if self.delay_seconds < 0:
            raise ValueError("Задержка не может быть отрицательной")
        if self.noise_level < 0:
            raise ValueError("Уровень шума не может быть отрицательным")
        if self.seed is not None:
            random.seed(self.seed)

    @classmethod
    def from_mapping(
        cls, sensors: Mapping[str, Tuple[float, float]], **kwargs: object
    ) -> "StreamConfig":
        mapped: Dict[str, SensorSpecification] = {
            name: SensorSpecification(nominal, spread) for name, (nominal, spread) in sensors.items()
        }
        return cls(sensors=mapped, **kwargs)


@dataclass
class AnalyzerConfig:
    """Глобальные параметры работы анализатора."""

    smoothing_factor: float = 0.3
    feature_window: int = 16
    learning_rate: float = 0.05
    l2_penalty: float = 1e-4
    max_records: int = 1000
    steps: int = 200

    def copy(self) -> "AnalyzerConfig":
        return dataclasses.replace(self)
