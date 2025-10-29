from __future__ import annotations

import asyncio
import logging
from typing import Dict

from .analyzer import RealTimeAnalyzer
from .config import AnalyzerConfig, SensorSpecification, StreamConfig
from .data_stream.simulator import DataStreamSimulator
from .features.engineering import FeatureEngineer
from .metrics import summarize_reports
from .models.anomaly import AnomalyDetector
from .models.logistic import IncrementalLogisticModel
from .models.twin import DigitalTwinModel
from .preprocessing.pipeline import PreprocessingPipeline
from .repository.state import StateRepository


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def build_analyzer() -> RealTimeAnalyzer:
    sensors: Dict[str, SensorSpecification] = {
        "temperature": SensorSpecification(630.0, 80.0),
        "pressure": SensorSpecification(18.0, 6.0),
        "vibration": SensorSpecification(3.0, 1.2),
        "load": SensorSpecification(0.75, 0.2),
    }

    stream_config = StreamConfig(sensors=sensors, anomaly_probability=0.07, delay_seconds=0.02, seed=42)
    analyzer_config = AnalyzerConfig(smoothing_factor=0.35, feature_window=12, learning_rate=0.08, steps=200)

    stream = DataStreamSimulator(stream_config)
    preprocessing = PreprocessingPipeline(smoothing_factor=analyzer_config.smoothing_factor)
    feature_engineer = FeatureEngineer(window=analyzer_config.feature_window)
    classifier = IncrementalLogisticModel(learning_rate=analyzer_config.learning_rate)
    twin = DigitalTwinModel(reference=sensors)
    anomaly_detector = AnomalyDetector()
    repository = StateRepository(max_records=analyzer_config.max_records)

    return RealTimeAnalyzer(
        stream=stream,
        preprocessing=preprocessing,
        feature_engineer=feature_engineer,
        classifier=classifier,
        twin_model=twin,
        anomaly_detector=anomaly_detector,
        repository=repository,
        config=analyzer_config,
    )


async def main() -> None:
    configure_logging()
    analyzer = await build_analyzer()

    logging.info("Запуск цикла обработки в режиме реального времени")
    await analyzer.run()

    repository = analyzer.repository
    summary = summarize_reports(repository)
    logging.info("Средний индекс состояния: %0.3f", summary.average_health)
    logging.info("Доля критических аномалий: %0.3f", summary.anomaly_ratio)
    logging.info("Средняя вероятность критики: %0.3f", summary.critical_probability)

    last_report = repository.last()
    if last_report:
        logging.info(
            "Последнее состояние: вероятность критики=%0.3f, класс=%d",
            last_report.probability,
            last_report.predicted_class,
        )


if __name__ == "__main__":
    asyncio.run(main())
