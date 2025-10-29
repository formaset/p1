from __future__ import annotations

import logging
from typing import AsyncIterator

from .config import AnalyzerConfig
from .data_stream.simulator import DataStreamSimulator, SensorRecord
from .features.engineering import FeatureEngineer
from .models.anomaly import AnomalyDetector
from .models.logistic import IncrementalLogisticModel
from .models.twin import DigitalTwinModel
from .repository.state import ClassificationReport, StateRepository
from .preprocessing.pipeline import PreprocessingPipeline


class RealTimeAnalyzer:
    """Связывает подготовку данных, цифровой двойник и классификатор."""

    def __init__(
        self,
        stream: DataStreamSimulator,
        preprocessing: PreprocessingPipeline,
        feature_engineer: FeatureEngineer,
        classifier: IncrementalLogisticModel,
        twin_model: DigitalTwinModel,
        anomaly_detector: AnomalyDetector,
        repository: StateRepository,
        config: AnalyzerConfig,
    ) -> None:
        self._stream = stream
        self._preprocessing = preprocessing
        self._feature_engineer = feature_engineer
        self._classifier = classifier
        self._twin = twin_model
        self._anomaly_detector = anomaly_detector
        self._repository = repository
        self._config = config

    async def run(self) -> None:
        iterator = self._stream.stream()
        async for _ in self._iterate(iterator, self._config.steps):
            pass

    @property
    def repository(self) -> StateRepository:
        return self._repository

    async def _iterate(
        self, iterator: AsyncIterator[SensorRecord], steps: int
    ) -> AsyncIterator[ClassificationReport]:
        for _ in range(steps):
            record = await iterator.__anext__()
            cleaned = self._preprocessing.apply(record)
            features = self._feature_engineer.transform(cleaned)
            assessment = self._twin.evaluate(cleaned)

            anomalies = self._anomaly_detector.register(cleaned)
            probability = self._classifier.predict_proba(features)
            threshold = self._adaptive_threshold(assessment.health_index)
            predicted_class = int(probability >= threshold)

            target = 1 if assessment.health_index < 0.7 else 0
            self._classifier.partial_fit(features, target)
            probability = self._classifier.predict_proba(features)
            predicted_class = int(probability >= threshold)

            report = ClassificationReport(
                probability=probability,
                predicted_class=predicted_class,
                anomalies=anomalies,
                health_index=assessment.health_index,
            )
            self._repository.push(report)
            yield report

            logging.debug(
                "Поступил пакет: вероятность=%0.3f, здоровье=%0.3f, аномалии=%s",
                probability,
                assessment.health_index,
                {k: round(v, 2) for k, v in anomalies.items()},
            )

    @staticmethod
    def _adaptive_threshold(health_index: float) -> float:
        return max(0.3, min(0.8, 0.6 - 0.3 * (1.0 - health_index)))


async def execute_pipeline(analyzer: RealTimeAnalyzer) -> StateRepository:
    await analyzer.run()
    return analyzer.repository
