# Data Dictionary & Schema Specification — BuildTrust AI

All data models are strictly defined and validated via Pydantic v2 models. Timestamps are formatted in ISO-8601 UTC.

---

## 1. Release Manifest Model (`ReleaseCreate` / `ReleaseResponse`)

| Field | Type | Description | Constraints |
|---|---|---|---|
| `project_id` | string | Unique project identifier | 2–64 alphanumeric, dash, underscore |
| `release_id` | string | Unique release identifier | 2–64 alphanumeric, dash, period |
| `version` | string | Semantic or calendar version | e.g. `1.0.0` |
| `source_commit` | string | Git commit SHA | Min length 4, hex string |
| `artifact.filename` | string | Release binary filename | Sanitized, no path traversal |
| `artifact.expected_sha256` | string | Cryptographic reference digest | Exactly 64 hex characters |
| `artifact.size_bytes` | integer | Size of the artifact in bytes | Non-negative integer |
| `evidence_requirements` | object | Flags for required evidence | Booleans for SBOM, Provenance, Tests, Scan |
| `policy_version` | string | Applicable policy version | Default `1.0` |
| `environment` | string | Release target environment | `development`, `staging`, `production`, `test` |

---

## 2. Canonical Evidence Envelope (`EvidenceEnvelope`)

| Field | Type | Description | Constraints |
|---|---|---|---|
| `evidence_id` | string | Unique evidence identifier | e.g. `ev-0001` |
| `project_id` | string | Associated project identifier | Must match release |
| `release_id` | string | Associated release identifier | Must match release |
| `evidence_type` | string | Classification of evidence | `artifact_integrity`, `sbom`, `vulnerability_scan`, `provenance`, `test_results`, `policy_change` |
| `schema_version` | string | Evidence schema format version | Default `1.0` |
| `evidence_version` | integer | Sequential version per type | $\ge 1$ |
| `source` | string | Submitting tool/agent | e.g. `artifact_verifier`, `osv-scanner` |
| `observed_at` | string | UTC timestamp when observed | ISO-8601 |
| `received_at` | string | UTC timestamp when ingested | ISO-8601 |
| `validation_status` | string | Validation outcome | `valid`, `invalid`, `unverified`, `quarantined` |
| `payload` | object | Typed evidence content | Validated per `evidence_type` |
| `content_sha256` | string | Deterministic JSON payload hash | Exactly 64 hex characters (deduplication key) |
| `correlation_id` | string | Distributed trace correlation | Alphanumeric |

---

## 3. Assessment Record (`AssessmentRecord`)

| Field | Type | Description |
|---|---|---|
| `assessment_id` | string | Unique assessment identifier (e.g. `asm-a1b2c3d4e5`) |
| `project_id` | string | Associated project identifier |
| `release_id` | string | Associated release identifier |
| `assessment_version` | integer | Sequential assessment version (increments upon evidence change) |
| `trust_score` | float / null | Composite score ($0.0 \le T \le 100.0$) or null if insufficient |
| `decision` | string | Release gate outcome (`APPROVE`, `REVIEW`, `BLOCK`, `INSUFFICIENT_EVIDENCE`) |
| `score_breakdown` | object | Numerical component scores ($I, D, P, S, E$) and weight details |
| `blocking_reasons` | list[string] | Human-readable mandatory gate failure explanations |
| `risk_factors` | list[string] | Identified risk signals and concentration warnings |
| `recommendations` | list[string] | Prescriptive remediation steps |
| `explanations` | list[object] | Evidence-grounded policy rule explanation items |
| `ai_anomaly` | object | IsolationForest anomaly flag, score, and feature summary |
| `evidence_ids_used` | list[string] | List of evidence envelope IDs evaluated in this assessment |
| `previous_assessment_id` | string / null | Pointer to immediately preceding assessment |
| `created_at` | string | Assessment computation timestamp (ISO-8601 UTC) |

---

## 4. DynamoDB Single-Table Design (`BuildTrustRecords`)

| Entity | Partition Key (PK) | Sort Key (SK) | Description |
|---|---|---|---|
| **Project** | `PROJECT#<project_id>` | `METADATA` | Project name, policy rules, timestamps |
| **Release** | `PROJECT#<project_id>` | `RELEASE#<release_id>` | Candidate manifest, latest decision & score |
| **Evidence** | `RELEASE#<release_id>` | `EVIDENCE#<timestamp>#<id>` | Canonical evidence envelopes |
| **Assessment** | `RELEASE#<release_id>` | `ASSESSMENT#<version>` | Versioned assessment record snapshot |
| **Audit Event** | `RELEASE#<release_id>` | `AUDIT#<timestamp>#<id>` | State transition change event |
| **User** | `USER#<email>` | `METADATA` | User credentials, role, active status |
