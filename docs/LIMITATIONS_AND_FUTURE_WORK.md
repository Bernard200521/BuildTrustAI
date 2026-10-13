# Limitations and Future Work — BuildTrust AI

To preserve scientific and engineering integrity, we explicitly distinguish between **implemented functionality** and **planned future enhancements**.

---

## 1. Implemented Functionality (Working in Prototype)

1. **Evidence-Change Trust Engine (ECTE):**
   - Versioned assessment history and delta detection.
   - Idempotent submission deduplication via deterministic JSON payload hashing.
   - Composite weighted score calculation ($T = 0.25I + 0.20D + 0.20P + 0.15S + 0.20E$).
2. **Security Engineering:**
   - Real streaming SHA-256 calculation for large binary files without memory exhaustion.
   - CycloneDX JSON SBOM parsing, component extraction, and duplicate detection.
   - OSV.dev live API query with error handling and labeled offline fallback data.
   - SLSA v1.0 and in-toto provenance parsing with Cosign verification status tracking (`VERIFIED`, `FAILED`, `UNVERIFIED`, `NOT_PERFORMED`).
   - Strict deterministic policy gates (`APPROVE`, `REVIEW`, `BLOCK`, `INSUFFICIENT_EVIDENCE`).
3. **AI Engineering:**
   - Transparent, evidence-grounded human explanations for each factor and decision change.
   - Locally executable scikit-learn `IsolationForest` model for multidimensional anomaly detection.
   - Failsafe fallback if the ML model file is missing.
4. **Cloud & Data Engineering:**
   - Single-table Amazon DynamoDB repository adapter and encrypted Amazon S3 vault adapter.
   - Seamless local development mode (`STORAGE_BACKEND=local`) with zero cloud dependencies.
   - AWS SAM CloudFormation template, App Runner configuration, and IAM least-privilege policies.
5. **Frontend:**
   - Responsive enterprise React dashboard with 7 views, Recharts visual graphs, and live Server-Sent Events (SSE) updates.

---

## 2. Documented Limitations & Prototype Assumptions

1. **Synthetic Training Benchmark:**
   The `IsolationForest` model was trained on a reproducible synthetic dataset representing typical clean vs anomalous release feature distributions. It should not be represented as a model trained on real production telemetry.
2. **In-Process SSE Event Broadcaster:**
   The live event broadcaster uses in-process asyncio subscriber queues. This is suitable for single-instance FastAPI deployments (such as our App Runner container or local server), but multi-instance clustered deployments require a distributed pub/sub broker (such as Amazon SQS, SNS, or Redis Pub/Sub).
3. **Cosign Cryptographic Verification:**
   Cosign verification evaluates configured attestation keys and claims. Integration with Sigstore's public Rekor transparency log and Fulcio OIDC certificates is documented as an enhancement.

---

## 3. Future Work

1. **Distributed Event Fabric:**
   Integrate Amazon EventBridge and SQS to decouple evidence ingestion workers from evaluation engines across distributed microservices.
2. **eBPF Runtime Trace Correlation:**
   Correlate release evidence with post-deployment eBPF telemetry to verify that running container behaviors match declared SBOM and provenance attestations.
3. **Automated Remediation Workflows:**
   Provide automated GitHub Pull Request generation for vulnerable packages identified by OSV advisories.
