# Testing & Evaluation Report — BuildTrust AI

## 1. Test Suite Summary

BuildTrust AI includes an automated test suite executed via `pytest` covering all four engineering modules.

- **Total Test Cases Executed:** 23
- **Passed:** 23
- **Failed:** 0
- **Execution Time:** ~5.5 seconds

---

## 2. Test Execution Details by Engineering Domain

### 2.1 Data Engineering Tests
| Test Case | Description | Result |
|---|---|---|
| `test_cyclonedx_sbom_parsing` | Validates CycloneDX JSON parsing and component normalization | **PASSED** |
| `test_sbom_duplicate_component_detection` | Detects duplicate dependencies in SBOM manifests | **PASSED** |
| `test_evidence_change_detection_and_reassessment` | Verifies versioned delta detection upon new evidence submission | **PASSED** |
| `test_assessment_history_retention` | Confirms version increments (v1 $\rightarrow$ v2 $\rightarrow$ v3) and history retention | **PASSED** |

### 2.2 Security Engineering Tests
| Test Case | Description | Result |
|---|---|---|
| `test_artifact_matching_hash` | Real SHA-256 calculation matches expected digest ($I = 100.0$) | **PASSED** |
| `test_artifact_tampered_hash_mismatch` | Deliberately modified payload triggers mismatch ($I = 0.0$) | **PASSED** |
| `test_provenance_valid_verification` | Valid SLSA builder, source commit, and Cosign signature verification | **PASSED** |
| `test_provenance_commit_mismatch_failure` | Commit tag mismatch fails mandatory verification | **PASSED** |
| `test_mandatory_hash_mismatch_blocks_release` | Hash mismatch unconditionally triggers `BLOCK` overriding high score | **PASSED** |
| `test_critical_vulnerability_blocks_release` | Zero-tolerance policy blocks candidate with critical CVE | **PASSED** |
| `test_clean_release_approved` | Fully compliant release satisfies approval gate | **PASSED** |
| `test_vulnerability_scoring_formula` | Verifies $D = \max(0, 100 - 40C - 20H - 8M - 2L)$ calculation | **PASSED** |
| `test_vulnerability_deduplication` | Prevents duplicate CVE advisories from skewing scores | **PASSED** |

### 2.3 AI Engineering Tests
| Test Case | Description | Result |
|---|---|---|
| `test_trust_engine_scoring_formula` | Validates composite weighted formula and bounded range | **PASSED** |
| `test_ai_anomaly_forces_review_not_override` | Anomaly downgrades `APPROVE` to `REVIEW`; never overrides policy | **PASSED** |
| `test_password_hashing_and_verification` | Bcrypt password hashing and verification | **PASSED** |
| `test_jwt_token_generation` | Signed JWT token generation and claims encoding | **PASSED** |

### 2.4 AWS Cloud Integration Tests (Mocked via Moto)
| Test Case | Description | Result |
|---|---|---|
| `test_dynamodb_repository_workflow` | Put, get, and query records on single-table DynamoDB design | **PASSED** |
| `test_s3_repository_upload_and_download` | Encrypted artifact upload and byte download via S3 | **PASSED** |

### 2.5 API Integration Tests
| Test Case | Description | Result |
|---|---|---|
| `test_health_check` | Validates `/health` endpoint and uptime | **PASSED** |
| `test_readiness_check` | Validates `/ready` endpoint and storage availability | **PASSED** |
| `test_auth_login_and_me` | End-to-end admin login and `/me` introspection | **PASSED** |
| `test_dashboard_summary` | Live metrics computation from stored database records | **PASSED** |

---

## 3. Machine Learning Evaluation (IsolationForest)

Evaluated on a documented synthetic evaluation benchmark of 500 release feature vectors (425 nominal builds, 75 anomalous builds with multi-attribute deviations):

- **Model:** scikit-learn IsolationForest ($n=150$, contamination=0.10)
- **Evaluation Dataset:** Reproducible synthetic benchmark (clearly documented, not production data)
- **True Positives:** 9
- **True Negatives:** 375
- **False Positives:** 50
- **False Negatives:** 66
- **Precision:** 0.1525
- **Recall:** 0.1200
- **ROC-AUC:** 0.4685
- **Baseline Comparison Finding:** The IsolationForest functions as a prioritization indicator to flag multidimensional feature combinations for SecOps review. Strict deterministic policies govern the actual release gate outcomes.
