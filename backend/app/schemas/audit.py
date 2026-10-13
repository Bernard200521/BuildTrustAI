from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field

EventType = Literal[
    "EVIDENCE_SUBMITTED",
    "ARTIFACT_VERIFIED",
    "ASSESSMENT_CHANGED",
    "POLICY_BLOCK_TRIGGERED",
    "AI_ANOMALY_FLAGGED",
    "RELEASE_CREATED",
    "POLICY_UPDATED"
]

class AuditEvent(BaseModel):
    event_id: str
    event_type: EventType
    project_id: str
    release_id: str
    previous_assessment_version: Optional[int] = None
    new_assessment_version: Optional[int] = None
    previous_decision: Optional[str] = None
    new_decision: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    timestamp: str
    actor: str = "system"
    details: Dict[str, Any] = Field(default_factory=dict)

class AuditList(BaseModel):
    items: List[AuditEvent]
    total: int
