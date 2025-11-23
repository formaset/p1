"""Оркестрация всех компонентов конвейера."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Callable, Optional

from .anomaly import AnomalyDetector
from .classifier import Classification, WeightedClassifier
from .config import PipelineConfig
from .preprocessing import NormalizedEvent, PreprocessingPipeline
from .storage import Archivist, MemoryBuffer, StoredRecord
from .stream import BufferedStream, TelemetryStream
from .telemetry import TelemetryEvent

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Результат единичного шага конвейера."""

    original: TelemetryEvent
    normalized: NormalizedEvent
    classification: Classification


class Pipeline:
    """Собранный конвейер из стрима, препроцессинга и классификатора."""

    def __init__(self, config: PipelineConfig, on_result: Optional[Callable[[PipelineResult], None]] = None) -> None:
        self.config = config
        self.stream = TelemetryStream(config.stream)
        self.buffered_stream = BufferedStream(self.stream)
        self.preprocessing = PreprocessingPipeline(window=config.anomaly.window)
        self.anomaly = AnomalyDetector(config.anomaly)
        self.classifier = WeightedClassifier(config.classifier)
        self.archivist = Archivist(config.storage)
        self.memory_buffer = MemoryBuffer(config.storage.max_records_in_memory)
        self.on_result = on_result

    async def start(self, iterations: int | None = None) -> None:
        """Главный цикл обработки. iterations ограничивает количество шагов."""
        self.buffered_stream.start()
        counter = 0
        async for event in self.stream:
            result = self._process_event(event)
            if self.on_result:
                try:
                    self.on_result(result)
                except Exception:  # noqa: BLE001
                    logger.exception("Ошибка при пользовательском обратном вызове")
            counter += 1
            if iterations and counter >= iterations:
                logger.info("Достигнут лимит итераций: %s", iterations)
                break
        self.stream.stop()

    def _process_event(self, event: TelemetryEvent) -> PipelineResult:
        normalized = self.preprocessing.process(event)
        anomaly_result = self.anomaly.evaluate(normalized)
        classification = self.classifier.classify(normalized, anomaly_result)
        stored = StoredRecord(event=normalized, classification=classification)
        self.memory_buffer.push(stored)
        # Архивируем половину буфера при переполнении, чтобы не потерять данные
        if len(self.memory_buffer._records) >= self.memory_buffer.capacity:  # noqa: SLF001
            archive, rest = self.memory_buffer.split_for_archiving()
            self.archivist.append(archive)
            self.memory_buffer._records = rest  # noqa: SLF001
        return PipelineResult(original=event, normalized=normalized, classification=classification)

    def export_recent(self, limit: int = 10) -> list[StoredRecord]:
        """Достаёт последние обработанные записи."""
        return self.memory_buffer.snapshot(limit)

    async def run_for(self, seconds: float) -> None:
        """Запуск обработки на заданное количество секунд."""
        try:
            await asyncio.wait_for(self.start(), timeout=seconds)
        except asyncio.TimeoutError:
            logger.info("Истекло отведённое время %s секунд", seconds)
            self.stream.stop()


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
