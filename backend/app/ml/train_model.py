"""
Train IsolationForest model on reproducible synthetic release verification data.
NOTE: This dataset represents a documented synthetic benchmark representing typical
clean vs anomalous software release profiles for research & demonstration purposes.
It is NOT presented as real production telemetry data.
"""

import os
import json
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from backend.app.ml.feature_builder import FEATURE_NAMES

def generate_synthetic_dataset(n_samples: int = 1000, seed: int = 42) -> np.ndarray:
    rng = np.random.RandomState(seed)

    # 85% Normal Releases (healthy builds, matching hashes, good provenance, low/zero vulns)
    n_normal = int(n_samples * 0.85)
    norm_c = rng.choice([0.0, 0.0, 0.0, 0.2], size=n_normal)
    norm_h = rng.choice([0.0, 0.1, 0.0, 0.2], size=n_normal)
    norm_m = rng.uniform(0.0, 0.3, size=n_normal)
    max_sev = rng.choice([0.0, 1.0, 2.0], p=[0.6, 0.3, 0.1], size=n_normal)
    int_code = np.ones(n_normal) # Matching hash
    prov_code = np.ones(n_normal) # Valid provenance
    completeness = rng.uniform(85.0, 100.0, size=n_normal)
    test_pass = rng.uniform(92.0, 100.0, size=n_normal)
    test_mand = np.ones(n_normal)
    delta_vulns = rng.choice([0.0, 1.0, -1.0, 0.0], size=n_normal)
    changed_items = rng.choice([1.0, 2.0, 3.0], size=n_normal)

    normal_data = np.column_stack([
        norm_c, norm_h, norm_m, max_sev, int_code, prov_code,
        completeness, test_pass, test_mand, delta_vulns, changed_items
    ])

    # 15% Anomalous Releases (tampered hashes, sudden vulnerability spikes, missing provenance, failed tests)
    n_anom = n_samples - n_normal
    anom_c = rng.choice([0.4, 0.8, 1.0], size=n_anom)
    anom_h = rng.choice([0.5, 0.8, 1.0], size=n_anom)
    anom_m = rng.uniform(0.5, 1.0, size=n_anom)
    anom_sev = rng.choice([3.0, 4.0], size=n_anom)
    anom_int = rng.choice([0.0, 1.0], p=[0.4, 0.6], size=n_anom) # Tampering
    anom_prov = rng.choice([0.0, 1.0], p=[0.5, 0.5], size=n_anom) # Missing prov
    anom_comp = rng.uniform(20.0, 75.0, size=n_anom)
    anom_test = rng.uniform(40.0, 85.0, size=n_anom)
    anom_mand = rng.choice([0.0, 1.0], p=[0.6, 0.4], size=n_anom)
    anom_delta = rng.uniform(5.0, 25.0, size=n_anom) # Sudden vulnerability influx
    anom_changed = rng.uniform(4.0, 10.0, size=n_anom)

    anom_data = np.column_stack([
        anom_c, anom_h, anom_m, anom_sev, anom_int, anom_prov,
        anom_comp, anom_test, anom_mand, anom_delta, anom_changed
    ])

    dataset = np.vstack([normal_data, anom_data])
    rng.shuffle(dataset)
    return dataset

def train_and_save_model(output_path: str = "backend/app/ml/models/isolation_forest.joblib"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    X = generate_synthetic_dataset(n_samples=1200, seed=42)

    model = IsolationForest(
        n_estimators=150,
        contamination=0.10,
        max_samples="auto",
        random_state=42,
        n_jobs=-1
    )
    model.fit(X)

    # Save model
    joblib.dump(model, output_path)
    print(f"Model successfully trained and saved to {output_path}")

    # Compute baseline score on sample
    scores = model.decision_function(X)
    preds = model.predict(X)
    n_detected = np.sum(preds == -1)
    print(f"Evaluation: Detected {n_detected} / {len(X)} as anomalies ({round(n_detected/len(X)*100, 1)}%)")

    # Save metadata
    metadata_path = output_path.replace(".joblib", "_meta.json")
    meta = {
        "model_type": "IsolationForest",
        "n_estimators": 150,
        "features": FEATURE_NAMES,
        "n_training_samples": len(X),
        "contamination": 0.10,
        "dataset_type": "reproducible_synthetic_demonstration_benchmark",
        "caveat": "Anomaly scores are release prioritization signals and do NOT override deterministic security policies."
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

if __name__ == "__main__":
    train_and_save_model()
