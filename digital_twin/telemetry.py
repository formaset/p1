"""Модели данных для телеметрии."""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable


@dataclass
class TelemetryEvent:
    """Единичное событие телеметрии."""

    timestamp: float
    temperature: float
    vibration: float
    pressure: float
    payload: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, float]:
        """Преобразование в словарь для сериализации."""
        return {
            "timestamp": self.timestamp,
            "temperature": self.temperature,
            "vibration": self.vibration,
            "pressure": self.pressure,
            **self.payload,
        }

    @classmethod
    def synthetic(cls, t: float) -> "TelemetryEvent":
        """Генерация синтетических данных с лёгкой стохастикой."""
        # Используем плавные колебания, имитирующие работу механизмов
        temperature = 60 + 10 * math.sin(t / 5) + random.uniform(-2, 2)
        vibration = 3 + 2 * math.sin(t / 8) + random.uniform(-0.5, 0.5)
        pressure = 10 + 3 * math.cos(t / 6) + random.uniform(-0.4, 0.4)
        payload = {
            "энергопотребление": 30 + 5 * math.sin(t / 10) + random.uniform(-1, 1),
            "скорость": 1200 + 100 * math.sin(t / 12) + random.uniform(-20, 20),
        }
        return cls(timestamp=time.time(), temperature=temperature, vibration=vibration, pressure=pressure, payload=payload)


def batch_synthetic(count: int) -> Iterable[TelemetryEvent]:
    """Пакетная генерация синтетических событий для тестов."""
    start = time.time()
    for i in range(count):
        yield TelemetryEvent.synthetic(start + i)
