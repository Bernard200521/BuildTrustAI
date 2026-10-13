from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ArtifactDescriptor(BaseModel):
    filename: str = Field(..., min_length=1, max_length=256)
    s3_key: Optional[str] = None
    expected_sha256: str = Field(..., min_length=64, max_length=64, pattern=r"^[a-fA-F0-9]{64}$")
    size_bytes: Optional[int] = Field(default=None, ge=0)
    download_url: Optional[str] = None

class EvidenceRequirements(BaseModel):
    sbom_required: bool = True
    provenance_required: bool = True
    tests_required: bool = True
    dependency_scan_required: bool = True

class ReleaseCreate(BaseModel):
    project_id: str = Field(..., min_length=2, max_length=64)
    release_id: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    version: str = Field(..., min_length=1, max_length=64)
    source_commit: str = Field(..., min_length=4, max_length=64)
    artifact: ArtifactDescriptor
    evidence_requirements: EvidenceRequirements = Field(default_factory=EvidenceRequirements)
    policy_version: str = "1.0"
    environment: str = Field(default="staging", pattern=r"^(development|staging|production|test)$")

class ReleaseResponse(BaseModel):
    release_id: str
    project_id: str
    version: str
    source_commit: str
    artifact: ArtifactDescriptor
    evidence_requirements: EvidenceRequirements
    policy_version: str
    environment: str
    created_at: str
    updated_at: str
    created_by: str
    latest_assessment_id: Optional[str] = None
    latest_decision: Optional[str] = "PENDING_ASSESSMENT"
    latest_trust_score: Optional[float] = None
    evidence_counts: Dict[str, int] = Field(default_factory=dict)

class ReleaseList(BaseModel):
    items: List[ReleaseResponse]
    total: int
