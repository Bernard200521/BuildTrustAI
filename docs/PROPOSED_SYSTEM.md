# Proposed System — BuildTrust AI

## 1. System Overview

BuildTrust AI proposes an integrated, event-driven release trust-verification architecture that correlates five continuous streams of software release evidence into an explainable, policy-controlled release gate.

Instead of treating software verification as a single gate passed during a CI runner execution, BuildTrust AI treats the trustworthiness of a release candidate as an **evolving state** that adapts whenever new security evidence is submitted or updated.

---

## 2. Core Modules

### 2.1 Evidence Ingestion & Envelope Normalization (Data Engineering)
- Accepts release manifests declaring target environments, expected artifact hashes, and required evidence types.
- Enforces a canonical **Evidence Envelope** (`evidence_id`, `project_id`, `release_id`, `evidence_type`, `payload`, `content_sha256`, `validation_status`, `received_at`).
- Performs deterministic JSON payload hashing and deduplicates repeated submissions to prevent redundant reassessments.

### 2.2 Multi-Vector Security Verification (Security Engineering)
- **Artifact Verifier:** Calculates streaming SHA-256 digests on binary archives, comparing results against trusted expected values to detect binary tampering.
- **SBOM Analyzer:** Validates CycloneDX JSON documents, extracts components and licenses, and detects duplicate packages.
- **Vulnerability Service:** Connects to OSV.dev REST API with rate-limiting and error handling, normalizing findings into structured advisories with CVSS scores and fixed versions.
- **Provenance Verifier:** Evaluates SLSA v1.0 builder identities, source git commit tags, artifact digests, and optional Cosign cryptographic signatures.
- **Test Result Analyzer:** Assesses mandatory security regression suites versus non-mandatory check pass rates.

### 2.3 Evidence-Change Trust Engine (AI & Decision Engineering)
- Dynamically recalculates release trust using the transparent composite formula:
  $$T = 0.25I + 0.20D + 0.20P + 0.15S + 0.20E$$
- Evaluates an `IsolationForest` anomaly prioritization model across multidimensional release feature vectors.
- Produces evidence-grounded human explanations for score shifts.
- Enforces strict deterministic security policies: mandatory gates (hash mismatches, critical vulnerabilities, provenance failures) override AI scores.

### 2.4 Cloud Persistence & Live Event Streaming (Cloud Engineering)
- Single-table Amazon DynamoDB design for metadata, evidence envelopes, versioned assessments, and immutable audit events.
- Encrypted Amazon S3 bucket for binary artifacts and SBOM vaults.
- Real-time Server-Sent Events (SSE) broadcaster streaming immediate state updates to an interactive React dashboard.
