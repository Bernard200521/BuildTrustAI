import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import joblib
from backend.app.schemas.assessment import AIAnomalyResult

logger = logging.getLogger(__name__)

class ModelInference:
    """
    ML model inference service for release anomaly detection.
    Safely degrades to fallback mode if model file is missing or corrupted.
    """

    def __init__(self, model_path: str = "backend/app/ml/models/isolation_forest.joblib", enabled: bool = True):
        self.model_path = model_path
        self.enabled = enabled
        self._model = None
        self._load_model()

    def _load_model(self):
        if not self.enabled:
            logger.info("ML inference is disabled via configuration.")
            return

        if os.path.exists(self.model_path):
            try:
                self._model = joblib.load(self.model_path)
                logger.info("Successfully loaded ML IsolationForest model from %s", self.model_path)
            except Exception as e:
                logger.error("Failed to load ML model from %s: %s", self.model_path, str(e))
                self._model = None
        else:
            logger.warning("ML model file not found at %s. Operating in baseline fallback mode.", self.model_path)
            self._model = None

    def predict_anomaly(self, feature_vector: List[float]) -> AIAnomalyResult:
        """
        Evaluate feature vector using IsolationForest.
        Returns AIAnomalyResult with prioritization signal.
        """
        if not self.enabled or self._model is None:
            return AIAnomalyResult(
                anomaly_detected=False,
                anomaly_score=0.0,
                model_version="Fallback-Baseline",
                model_available=False,
                feature_importance_summary="ML model unavailable; using rule-based deterministic scoring only.",
                confidence_note="Baseline scoring active. Mandatory security gates remain fully enforced."
            )

        try:
            X = np.array([feature_vector])
            # IsolationForest: decision_function returns negative values for anomalies, positive for normal
            raw_score = float(self._model.decision_function(X)[0])
            pred = int(self._model.predict(X)[0]) # -1 = anomaly, 1 = normal
            is_anomaly = (pred == -1)

            # Map raw score to normalized prioritization indicator [0.0, 1.0]
            # typical decision function is in [-0.5, 0.5]
            normalized_score = round(max(0.0, min(1.0, 0.5 - raw_score)), 3)

            summary = []
            if feature_vector[0] > 0 or feature_vector[1] > 0:
                summary.append("Elevated vulnerability concentration")
            if feature_vector[4] == 0.0:
                summary.append("Artifact digest mismatch")
            if feature_vector[5] == 0.0:
                summary.append("Provenance verification failure")
            if feature_vector[9] > 3.0:
                summary.append("Sudden increase in disclosed vulnerabilities")

            feat_summary = "; ".join(summary) if summary else "Metrics consistent with nominal release baseline"

            return AIAnomalyResult(
                anomaly_detected=is_anomaly,
                anomaly_score=normalized_score,
                model_version="IsolationForest-v1.0",
                model_available=True,
                feature_importance_summary=feat_summary,
                confidence_note="Anomaly signal indicates unusual release profile for review prioritization. Deterministic security rules take absolute precedence."
            )
        except Exception as e:
            logger.error("Error during ML inference: %s", str(e))
            return AIAnomalyResult(
                anomaly_detected=False,
                anomaly_score=0.0,
                model_version="InferenceError-Fallback",
                model_available=False,
                feature_importance_summary=f"Inference error: {str(e)}",
                confidence_note="Failsafe: error in ML execution does not bypass security policies."
            )
