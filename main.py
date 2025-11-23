"""Точка входа для демонстрации системы анализа потоковых данных."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from digital_twin.config import DEFAULT_CONFIG, PipelineConfig
from digital_twin.orchestrator import Pipeline, PipelineResult, configure_logging
from digital_twin.telemetry import batch_synthetic


class ConsoleReporter:
    """Форматирование результатов в консоль."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def __call__(self, result: PipelineResult) -> None:
        cls = result.classification
        msg = (
            f"Класс: {cls.label.upper()} | Вероятность: {cls.probability:.2f} | "
            f"Причины: {', '.join(cls.rationale)} | T={result.original.temperature:.2f}"
        )
        logging.info(msg)
        if self.verbose:
            logging.debug("Нормализованные признаки: %s", result.normalized)


def parse_config(path: str | None) -> PipelineConfig:
    """Чтение пользовательской конфигурации из JSON."""
    if path is None:
        return DEFAULT_CONFIG
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Конфиг {path} не найден")
    data: dict[str, Any] = json.loads(cfg_path.read_text(encoding="utf-8"))
    # Простейшее восстановление dataclass из словаря
    return PipelineConfig(
        stream=DEFAULT_CONFIG.stream.__class__(**data.get("stream", {})),
        anomaly=DEFAULT_CONFIG.anomaly.__class__(**data.get("anomaly", {})),
        classifier=DEFAULT_CONFIG.classifier.__class__(**data.get("classifier", {})),
        storage=DEFAULT_CONFIG.storage.__class__(**data.get("storage", {})),
    )


def run_batch(config: PipelineConfig, count: int, verbose: bool) -> None:
    """Синхронная обработка ограниченного набора событий без асинхронного стрима."""
    reporter = ConsoleReporter(verbose=verbose)
    pipeline = Pipeline(config, on_result=reporter)
    for event in batch_synthetic(count):
        pipeline._process_event(event)  # noqa: SLF001
    logging.info("Пакетная обработка завершена, записей в буфере: %s", len(pipeline.memory_buffer.snapshot()))


def run_stream(config: PipelineConfig, seconds: float, verbose: bool) -> None:
    reporter = ConsoleReporter(verbose=verbose)
    pipeline = Pipeline(config, on_result=reporter)
    asyncio.run(pipeline.run_for(seconds))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Цифровой двойник: потоковый анализ данных")
    parser.add_argument("mode", choices=["stream", "batch"], help="Режим работы")
    parser.add_argument("--config", help="Путь до конфигурации в JSON", default=None)
    parser.add_argument("--seconds", type=float, default=10.0, help="Длительность работы для стрима")
    parser.add_argument("--count", type=int, default=50, help="Количество записей для пакетного режима")
    parser.add_argument("--verbose", action="store_true", help="Включить детализированный вывод")
    return parser


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()
    config = parse_config(args.config)
    if args.mode == "stream":
        run_stream(config, args.seconds, args.verbose)
    else:
        run_batch(config, args.count, args.verbose)


if __name__ == "__main__":
    main()
