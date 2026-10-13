from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, BinaryIO
from backend.app.schemas.project import ProjectResponse, ProjectCreate, ProjectPolicy
from backend.app.schemas.release import ReleaseResponse, ReleaseCreate
from backend.app.schemas.evidence import EvidenceEnvelope
from backend.app.schemas.assessment import AssessmentRecord
from backend.app.schemas.audit import AuditEvent

class BaseRepository(ABC):
    """Abstract interface defining the persistence layer for BuildTrust AI."""

    # Projects
    @abstractmethod
    def create_project(self, project: ProjectCreate, creator: str) -> ProjectResponse:
        pass

    @abstractmethod
    def get_project(self, project_id: str) -> Optional[ProjectResponse]:
        pass

    @abstractmethod
    def list_projects(self) -> List[ProjectResponse]:
        pass

    @abstractmethod
    def update_project_policy(self, project_id: str, policy: ProjectPolicy) -> Optional[ProjectResponse]:
        pass

    # Releases
    @abstractmethod
    def create_release(self, release: ReleaseCreate, creator: str) -> ReleaseResponse:
        pass

    @abstractmethod
    def get_release(self, release_id: str) -> Optional[ReleaseResponse]:
        pass

    @abstractmethod
    def list_releases(self, project_id: Optional[str] = None) -> List[ReleaseResponse]:
        pass

    @abstractmethod
    def update_release_status(self, release_id: str, decision: str, trust_score: Optional[float], assessment_id: str) -> Optional[ReleaseResponse]:
        pass

    # Evidence
    @abstractmethod
    def save_evidence(self, evidence: EvidenceEnvelope) -> EvidenceEnvelope:
        pass

    @abstractmethod
    def get_evidence(self, evidence_id: str) -> Optional[EvidenceEnvelope]:
        pass

    @abstractmethod
    def list_evidence_for_release(self, release_id: str) -> List[EvidenceEnvelope]:
        pass

    @abstractmethod
    def is_evidence_duplicate(self, release_id: str, evidence_type: str, content_sha256: str) -> bool:
        pass

    # Assessments
    @abstractmethod
    def save_assessment(self, assessment: AssessmentRecord) -> AssessmentRecord:
        pass

    @abstractmethod
    def get_latest_assessment(self, release_id: str) -> Optional[AssessmentRecord]:
        pass

    @abstractmethod
    def list_assessments(self, release_id: str) -> List[AssessmentRecord]:
        pass

    # Audit Events
    @abstractmethod
    def record_audit_event(self, event: AuditEvent) -> AuditEvent:
        pass

    @abstractmethod
    def list_audit_events(self, project_id: Optional[str] = None, release_id: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
        pass

    # Users / Auth
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    # Artifact Storage
    @abstractmethod
    def store_artifact(self, key: str, file_obj: BinaryIO) -> str:
        pass

    @abstractmethod
    def get_artifact_bytes(self, key: str) -> Optional[bytes]:
        pass
