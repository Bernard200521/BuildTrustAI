from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field

DecisionType = Literal[
    "APPROVE",
    "REVIEW",
    "BLOCK",
    "PENDING_ASSESSMENT",
    "INSUFFICIENT_EVIDENCE"
]

class ScoreComponentDetail(BaseModel):
    name: str
    weight: float
    score: Optional[float] = None # None indicates missing/insufficient
    status: Literal["VERIFIED", "FAILED", "MISSING", "PARTIAL", "NOT_REQUIRED"]
    details: str

class TrustScoreBreakdown(BaseModel):
    integrity_score: Optional[float] = Field(default=None, ge=0.0, le=100.0) # I (0.25)
    dependency_score: Optional[float] = Field(default=None, ge=0.0, le=100.0) # D (0.20)
    provenance_score: Optional[float] = Field(default=None, ge=0.0, le=100.0) # P (0.20)
    test_score: Optional[float] = Field(default=None, ge=0.0, le=100.0) # S (0.15)
    completeness_score: float = Field(default=0.0, ge=0.0, le=100.0) # E (0.20)
    formula: str = "T = 0.25*I + 0.20*D + 0.20*P + 0.15*S + 0.20*E"
    components: List[ScoreComponentDetail] = Field(default_factory=list)

class AIAnomalyResult(BaseModel):
    anomaly_detected: bool = False
    anomaly_score: float = 0.0 # Raw isolation forest score or normalized [0, 1]
    model_version: str = "IsolationForest-v1.0"
    model_available: bool = True
    feature_importance_summary: Optional[str] = None
    confidence_note: str = "Anomaly signal serves as prioritization indicator; deterministic policies govern release gates."

class ExplanationItem(BaseModel):
    rule_or_factor: str
    impact: Literal["BLOCK", "PENALTY", "NEUTRAL", "POSITIVE"]
    message: str
    evidence_ref: Optional[str] = None

class AssessmentRecord(BaseModel):
    assessment_id: str
    project_id: str
    release_id: str
    assessment_version: int = 1
    trust_score: Optional[float] = None
    decision: DecisionType
    policy_version: str = "1.0"
    score_breakdown: TrustScoreBreakdown
    blocking_reasons: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    explanations: List[ExplanationItem] = Field(default_factory=list)
    ai_anomaly: Optional[AIAnomalyResult] = None
    evidence_ids_used: List[str] = Field(default_factory=list)
    previous_assessment_id: Optional[str] = None
    created_at: str
    engine_version: str = "ECTE-v1.0"

class AssessmentHistory(BaseModel):
    release_id: str
    items: List[AssessmentRecord]
    total: int
