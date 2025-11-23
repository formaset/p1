"""Хранилище результатов и событий."""
from __future__ import annotations

import json
import pathlib
from dataclasses import asdict, dataclass, field
from typing import Iterable, List, Tuple

from .config import StorageConfig
from .classifier import Classification
from .preprocessing import NormalizedEvent


@dataclass
class StoredRecord:
    """Комбинация входа и результата классификации для архивации."""

    event: NormalizedEvent
    classification: Classification

    def to_dict(self) -> dict:
        return {
            "event": {
                "source": self.event.source.to_dict(),
                "normalized_temperature": self.event.normalized_temperature,
                "normalized_vibration": self.event.normalized_vibration,
                "normalized_pressure": self.event.normalized_pressure,
                "rolling_vector": self.event.rolling_vector,
            },
            "classification": asdict(self.classification),
        }


class Archivist:
    """Отвечает за долговременную запись данных на диск."""

    def __init__(self, config: StorageConfig) -> None:
        self.config = config
        self.path = pathlib.Path(config.persist_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, records: Iterable[StoredRecord]) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


class MemoryBuffer:
    """Хранение последних результатов для быстрых ответов."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._records: List[StoredRecord] = []

    def push(self, record: StoredRecord) -> None:
        if len(self._records) >= self.capacity:
            self._records.pop(0)
        self._records.append(record)

    def snapshot(self, limit: int | None = None) -> List[StoredRecord]:
        if limit is None:
            return list(self._records)
        return list(self._records[-limit:])

    def split_for_archiving(self) -> Tuple[List[StoredRecord], List[StoredRecord]]:
        half = len(self._records) // 2
        return self._records[:half], self._records[half:]
