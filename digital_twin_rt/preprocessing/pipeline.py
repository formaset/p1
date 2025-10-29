from __future__ import annotations

import math
import statistics
from collections import deque
from typing import Deque, Dict

from ..data_stream.simulator import SensorRecord


class PreprocessingPipeline:
    """Проводит фильтрацию и стабилизацию показаний сенсоров."""

    def __init__(self, smoothing_factor: float = 0.2) -> None:
        if not 0 < smoothing_factor <= 1:
            raise ValueError("Коэффициент сглаживания должен быть в диапазоне (0, 1]")
        self._smoothing = smoothing_factor
        self._last_values: Dict[str, float] = {}
        self._medians: Dict[str, Deque[float]] = {}

    def apply(self, record: SensorRecord) -> Dict[str, float]:
        processed: Dict[str, float] = {}
        for name, value in record.values.items():
            median_window = self._medians.setdefault(name, deque(maxlen=5))
            median_window.append(value)
            median = statistics.median(median_window)
            if not math.isfinite(value):
                value = median

            baseline = self._last_values.get(name, median)
            filtered = baseline + self._smoothing * (value - baseline)
            self._last_values[name] = filtered
            processed[name] = filtered
        return processed
