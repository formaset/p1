from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import AsyncIterator, Dict

from ..config import StreamConfig


@dataclass
class SensorRecord:
    """Снимок показаний системы в момент времени."""

    timestamp: float
    values: Dict[str, float]


class DataStreamSimulator:
    """Асинхронно формирует поток данных, имитируя работу оборудования."""

    def __init__(self, config: StreamConfig) -> None:
        self._config = config

    async def stream(self) -> AsyncIterator[SensorRecord]:
        sensors = self._config.sensors
        noise_level = self._config.noise_level
        anomaly_probability = self._config.anomaly_probability
        delay = self._config.delay_seconds

        while True:
            values: Dict[str, float] = {}
            for name, spec in sensors.items():
                noise = random.gauss(0.0, spec.spread * noise_level)
                value = random.gauss(spec.nominal, spec.spread / 4) + noise
                if random.random() < anomaly_probability:
                    value += spec.spread * random.choice([-3.5, 4.0])
                values[name] = value
            yield SensorRecord(timestamp=time.time(), values=values)
            await asyncio.sleep(delay)
