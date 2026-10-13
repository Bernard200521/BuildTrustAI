from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ProjectPolicy(BaseModel):
    approval_threshold: float = Field(default=85.0, ge=0.0, le=100.0)
    review_threshold: float = Field(default=60.0, ge=0.0, le=100.0)
    require_provenance: bool = True
    require_sbom: bool = True
    require_tests: bool = True
    require_dependency_scan: bool = True
    block_on_critical_vuln: bool = True
    block_on_high_vuln_count: int = 3
    block_on_hash_mismatch: bool = True
    require_cosign_verification: bool = False
    policy_version: str = "1.0"

class ProjectCreate(BaseModel):
    project_id: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = ""
    repository_url: Optional[str] = None
    policy: ProjectPolicy = Field(default_factory=ProjectPolicy)

class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = ""
    repository_url: Optional[str] = None
    policy: ProjectPolicy
    created_at: str
    updated_at: str
    created_by: str
    releases_count: int = 0

class ProjectList(BaseModel):
    items: List[ProjectResponse]
    total: int
