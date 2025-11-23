"""Модуль, реализующий симуляцию потоковой подачи событий."""
from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import AsyncIterator, Callable, Optional

from .config import StreamConfig
from .telemetry import TelemetryEvent

logger = logging.getLogger(__name__)


class TelemetryStream:
    """Асинхронный источник телеметрии."""

    def __init__(self, config: StreamConfig) -> None:
        self.config = config
        self._running = False
        self._subscribers: list[Callable[[TelemetryEvent], None]] = []

    def subscribe(self, callback: Callable[[TelemetryEvent], None]) -> None:
        """Регистрация слушателя для каждого события."""
        self._subscribers.append(callback)

    async def __aiter__(self) -> AsyncIterator[TelemetryEvent]:
        """Позволяет итерироваться по событиям в стиле async for."""
        async for event in self.start():
            yield event

    async def start(self) -> AsyncIterator[TelemetryEvent]:
        """Запуск бесконечной генерации событий."""
        if self._running:
            logger.warning("Стрим уже запущен")
            return
        self._running = True
        logger.info("Запуск потоковой симуляции")
        interval = 1.0 / self.config.frequency_hz
        while self._running:
            begin = time.monotonic()
            event = TelemetryEvent.synthetic(begin)
            for callback in list(self._subscribers):
                try:
                    callback(event)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Ошибка при обработке подписчика: %s", exc)
            yield event
            # Добавляем джиттер, чтобы имитировать нерегулярность транспорта
            elapsed = time.monotonic() - begin
            jitter = random.uniform(-self.config.jitter, self.config.jitter)
            await asyncio.sleep(max(0, interval + jitter - elapsed))

    def stop(self) -> None:
        """Остановка стрима."""
        self._running = False


class BufferedStream:
    """Буферизованный адаптер для стрима, сохраняющий последние события."""

    def __init__(self, source: TelemetryStream, max_size: Optional[int] = None) -> None:
        self.source = source
        self.max_size = max_size or source.config.max_queue
        self._queue: asyncio.Queue[TelemetryEvent] = asyncio.Queue(maxsize=self.max_size)
        self._task: Optional[asyncio.Task[None]] = None

    def start(self) -> None:
        """Запускает отдельную задачу приёма событий."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._consume())

    async def _consume(self) -> None:
        async for event in self.source:
            if self._queue.full():
                # Удаляем старейшее, чтобы не блокировать поток
                _ = self._queue.get_nowait()
            await self._queue.put(event)

    async def next_event(self) -> TelemetryEvent:
        """Получение следующего события из буфера."""
        return await self._queue.get()

    async def drain(self) -> AsyncIterator[TelemetryEvent]:
        """Чтение всех накопленных событий."""
        while not self._queue.empty():
            yield await self._queue.get()
