from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field

EvidenceType = Literal[
    "artifact_integrity",
    "sbom",
    "vulnerability_scan",
    "provenance",
    "test_results",
    "policy_change"
]

ValidationStatus = Literal["valid", "invalid", "unverified", "quarantined"]
CosignStatus = Literal["VERIFIED", "FAILED", "UNVERIFIED", "NOT_PERFORMED"]

class ArtifactIntegrityPayload(BaseModel):
    filename: str
    calculated_sha256: str = Field(..., pattern=r"^[a-fA-F0-9]{64}$")
    expected_sha256: str = Field(..., pattern=r"^[a-fA-F0-9]{64}$")
    matches: bool
    byte_size: int = Field(..., ge=0)
    verification_time_ms: Optional[float] = 0.0

class SBOMComponent(BaseModel):
    name: str
    version: str
    purl: Optional[str] = None
    type: Optional[str] = "library"
    license: Optional[str] = None

class SBOMPayload(BaseModel):
    format: str = "CycloneDX"
    spec_version: str = "1.5"
    component_count: int = Field(default=0, ge=0)
    components: List[SBOMComponent] = Field(default_factory=list)
    duplicate_components: List[str] = Field(default_factory=list)
    has_signature: bool = False

class VulnFinding(BaseModel):
    id: str
    package: str
    version: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    cvss_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    summary: Optional[str] = ""
    advisory_url: Optional[str] = None
    fixed_version: Optional[str] = None
    source: Optional[str] = "OSV"

class VulnerabilityScanPayload(BaseModel):
    scanner_name: str = "OSV-Scanner"
    scan_timestamp: str
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    findings: List[VulnFinding] = Field(default_factory=list)
    offline_fallback: bool = False

class ProvenancePayload(BaseModel):
    builder_id: str
    build_type: str = "https://slsa.dev/provenance/v1"
    source_revision: str
    artifact_digest: str
    slsa_level: Literal["SLSA_BUILD_LEVEL_0", "SLSA_BUILD_LEVEL_1", "SLSA_BUILD_LEVEL_2", "SLSA_BUILD_LEVEL_3"] = "SLSA_BUILD_LEVEL_2"
    invocation_entry_point: Optional[str] = None
    cosign_verified: CosignStatus = "NOT_PERFORMED"
    cosign_signer_identity: Optional[str] = None
    validation_notes: List[str] = Field(default_factory=list)

class TestSuiteResult(BaseModel):
    name: str
    passed: bool
    duration_seconds: Optional[float] = 0.0
    mandatory: bool = True

class TestResultsPayload(BaseModel):
    test_framework: str = "pytest"
    total_tests: int = Field(..., ge=0)
    passed: int = Field(..., ge=0)
    failed: int = Field(default=0, ge=0)
    skipped: int = Field(default=0, ge=0)
    mandatory_tests_passed: bool = True
    coverage_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    suites: List[TestSuiteResult] = Field(default_factory=list)

class EvidenceEnvelope(BaseModel):
    evidence_id: str = Field(..., min_length=2, max_length=64)
    project_id: str = Field(..., min_length=2, max_length=64)
    release_id: str = Field(..., min_length=2, max_length=64)
    evidence_type: EvidenceType
    schema_version: str = "1.0"
    evidence_version: int = Field(default=1, ge=1)
    source: str = Field(..., min_length=2, max_length=64)
    observed_at: str
    received_at: str
    validation_status: ValidationStatus = "valid"
    payload: Dict[str, Any] = Field(default_factory=dict)
    content_sha256: str = Field(..., min_length=64, max_length=64, pattern=r"^[a-fA-F0-9]{64}$")
    correlation_id: str = Field(..., min_length=2, max_length=64)

class EvidenceSubmission(BaseModel):
    evidence_id: Optional[str] = None
    evidence_type: EvidenceType
    source: str = "cli_agent"
    observed_at: Optional[str] = None
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None

class EvidenceList(BaseModel):
    items: List[EvidenceEnvelope]
    total: int
