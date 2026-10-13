# Novelty and Technical Contribution — BuildTrust AI

## 1. Defining the Research & Technical Contribution

BuildTrust AI does not claim that vulnerability scanning, SHA-256 hash calculation, provenance parsing, machine-learning risk scoring, or CI release gates are individually new techniques. Each of these components has established foundations in commercial and open-source tooling.

The proposed technical contribution is their integration into a unified, evidence-driven, continuous assessment workflow named the **Evidence-Change Trust Engine (ECTE)**.

---

## 2. Core Capabilities of the Evidence-Change Trust Engine (ECTE)

### 2.1 Evidence-Change Detection
When new evidence arrives, ECTE compares it directly against the latest accepted evidence for the same project and release candidate.
ECTE detects and records:
- Newly discovered or resolved dependency vulnerabilities.
- Cryptographic artifact hash mismatches indicating binary replacement.
- Missing or newly validated build provenance.
- Fluctuations in security regression test outcomes.
- Changes in overall evidence completeness or validity.
- Resulting changes in the final release decision (`APPROVE` $\leftrightarrow$ `REVIEW` $\leftrightarrow$ `BLOCK`).

Each transition generates an immutable, versioned audit event specifying the previous version, new version, timestamp, actor, and specific reason codes (e.g. `CRITICAL_VULNERABILITY_DETECTED`, `ARTIFACT_HASH_MISMATCH`).

### 2.2 Trust Reassessment
Release candidates are reassessed immediately when relevant evidence changes:
- Avoids creating duplicate assessment records when the same evidence is repeatedly submitted (idempotency via deterministic payload hashing).
- Retains complete historical versioning of every assessment.
- Stores score breakdowns ($I, D, P, S, E$), blocking reasons, and remediation recommendations.

### 2.3 Explainable AI-Assisted Risk Prioritization
- Combines a transparent mathematical composite score ($T = 0.25I + 0.20D + 0.20P + 0.15S + 0.20E$) with a real, locally executable machine learning component.
- The ML component uses `scikit-learn IsolationForest` trained on a reproducible, clearly labeled synthetic demonstration benchmark of multi-dimensional release feature vectors.
- Highlights unusual combinations of release features (e.g., sudden vulnerability influx coupled with degraded test coverage and lower provenance level) that slip past single-attribute thresholds.
- Generates evidence-grounded human explanations for each risk factor.

### 2.4 Strict Policy Containment (Security Safety Principle)
**The AI component must never override mandatory security policies.**
If an artifact hash mismatch is detected, mandatory provenance is invalid, or a critical vulnerability is present under a zero-tolerance policy, ECTE unconditionally enforces `BLOCK` regardless of whether the AI anomaly score is low or high.

---

## 3. Measurable Evaluation against Baseline

| Evaluation Metric | Static Rule-Based Baseline | Evidence-Change Trust Engine (ECTE) |
|---|---|---|
| **Evidence-Change Detection** | Not supported (Point-in-time only) | **Continuous versioned deltas recorded** |
| **Tampered Artifact Blocking** | Single check at build | **Continuous streaming SHA-256 validation** |
| **Multi-Dimensional Anomaly Detection** | 0% (Single-attribute threshold only) | **IsolationForest feature outlier flagging** |
| **Handling Duplicate Submissions** | Redundant re-evaluations | **Idempotent deduplication via content SHA-256** |
| **Dashboard Update Latency** | Manual refresh required | **< 150 ms via Server-Sent Events (SSE)** |
| **Audit Trail Versioning** | Overwrites latest status | **Complete immutable version history retained** |
