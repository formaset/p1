"""Конфигурация системы цифрового двойника."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class StreamConfig:
    """Параметры симуляции потоковых данных."""

    frequency_hz: float = 2.0
    jitter: float = 0.05
    max_queue: int = 2000


@dataclass
class AnomalyConfig:
    """Пороговые параметры для выявления аномалий."""

    temperature_limit: float = 85.0
    vibration_limit: float = 7.5
    pressure_limit: float = 16.0
    window: int = 50
    sensitivity: float = 0.35


@dataclass
class ClassifierConfig:
    """Настройки классификатора."""

    classes: List[str] = field(default_factory=lambda: [
        "норма",
        "предупреждение",
        "авария",
    ])
    weight_temperature: float = 0.4
    weight_vibration: float = 0.35
    weight_pressure: float = 0.25


@dataclass
class StorageConfig:
    """Опции для хранения результатов."""

    persist_path: str = "./data/archivist.jsonl"
    max_records_in_memory: int = 5000


@dataclass
class PipelineConfig:
    """Объединённая конфигурация всего конвейера."""

    stream: StreamConfig = field(default_factory=StreamConfig)
    anomaly: AnomalyConfig = field(default_factory=AnomalyConfig)
    classifier: ClassifierConfig = field(default_factory=ClassifierConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)


DEFAULT_CONFIG = PipelineConfig()
