import os
import json
import threading
from typing import Optional, List, Dict, Any, BinaryIO
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.project import ProjectResponse, ProjectCreate, ProjectPolicy
from backend.app.schemas.release import ReleaseResponse, ReleaseCreate
from backend.app.schemas.evidence import EvidenceEnvelope
from backend.app.schemas.assessment import AssessmentRecord
from backend.app.schemas.audit import AuditEvent
from backend.app.utils.timestamps import utc_now_iso
from backend.app.utils.validation import validate_safe_path

class LocalRepository(BaseRepository):
    """
    Local filesystem repository implementation.
    Stores data in organized JSON files and artifacts in a subfolder.
    Includes thread locking and atomic file saving for data consistency.
    """

    def __init__(self, storage_dir: str = "backend/data"):
        self.storage_dir = os.path.abspath(storage_dir)
        self.artifacts_dir = os.path.join(self.storage_dir, "artifacts")
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self._lock = threading.RLock()

        self._files = {
            "projects": os.path.join(self.storage_dir, "projects.json"),
            "releases": os.path.join(self.storage_dir, "releases.json"),
            "evidence": os.path.join(self.storage_dir, "evidence.json"),
            "assessments": os.path.join(self.storage_dir, "assessments.json"),
            "audit": os.path.join(self.storage_dir, "audit.json"),
            "users": os.path.join(self.storage_dir, "users.json"),
        }

        for path in self._files.values():
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f)

    def _read_data(self, key: str) -> List[Dict[str, Any]]:
        path = self._files[key]
        with self._lock:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []

    def _write_data(self, key: str, data: List[Dict[str, Any]]) -> None:
        path = self._files[key]
        temp_path = f"{path}.tmp"
        with self._lock:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, path)

    # ------------------ Projects ------------------
    def create_project(self, project: ProjectCreate, creator: str) -> ProjectResponse:
        projects = self._read_data("projects")
        for p in projects:
            if p["project_id"] == project.project_id:
                raise ValueError(f"Project with ID '{project.project_id}' already exists.")

        now = utc_now_iso()
        record = {
            "project_id": project.project_id,
            "name": project.name,
            "description": project.description,
            "repository_url": project.repository_url,
            "policy": project.policy.model_dump(),
            "created_at": now,
            "updated_at": now,
            "created_by": creator,
            "releases_count": 0
        }
        projects.append(record)
        self._write_data("projects", projects)
        return ProjectResponse(**record)

    def get_project(self, project_id: str) -> Optional[ProjectResponse]:
        projects = self._read_data("projects")
        for p in projects:
            if p["project_id"] == project_id:
                releases = self.list_releases(project_id=project_id)
                p["releases_count"] = len(releases)
                return ProjectResponse(**p)
        return None

    def list_projects(self) -> List[ProjectResponse]:
        projects = self._read_data("projects")
        result = []
        for p in projects:
            releases = self.list_releases(project_id=p["project_id"])
            p["releases_count"] = len(releases)
            result.append(ProjectResponse(**p))
        return result

    def update_project_policy(self, project_id: str, policy: ProjectPolicy) -> Optional[ProjectResponse]:
        projects = self._read_data("projects")
        for p in projects:
            if p["project_id"] == project_id:
                p["policy"] = policy.model_dump()
                p["updated_at"] = utc_now_iso()
                self._write_data("projects", projects)
                return ProjectResponse(**p)
        return None

    # ------------------ Releases ------------------
    def create_release(self, release: ReleaseCreate, creator: str) -> ReleaseResponse:
        releases = self._read_data("releases")
        for r in releases:
            if r["release_id"] == release.release_id:
                raise ValueError(f"Release with ID '{release.release_id}' already exists.")

        now = utc_now_iso()
        record = {
            "release_id": release.release_id,
            "project_id": release.project_id,
            "version": release.version,
            "source_commit": release.source_commit,
            "artifact": release.artifact.model_dump(),
            "evidence_requirements": release.evidence_requirements.model_dump(),
            "policy_version": release.policy_version,
            "environment": release.environment,
            "created_at": now,
            "updated_at": now,
            "created_by": creator,
            "latest_assessment_id": None,
            "latest_decision": "PENDING_ASSESSMENT",
            "latest_trust_score": None,
            "evidence_counts": {}
        }
        releases.append(record)
        self._write_data("releases", releases)
        return ReleaseResponse(**record)

    def get_release(self, release_id: str) -> Optional[ReleaseResponse]:
        releases = self._read_data("releases")
        for r in releases:
            if r["release_id"] == release_id:
                ev_list = self.list_evidence_for_release(release_id)
                counts: Dict[str, int] = {}
                for ev in ev_list:
                    counts[ev.evidence_type] = counts.get(ev.evidence_type, 0) + 1
                r["evidence_counts"] = counts
                return ReleaseResponse(**r)
        return None

    def list_releases(self, project_id: Optional[str] = None) -> List[ReleaseResponse]:
        releases = self._read_data("releases")
        results = []
        for r in releases:
            if project_id is None or r["project_id"] == project_id:
                ev_list = self.list_evidence_for_release(r["release_id"])
                counts: Dict[str, int] = {}
                for ev in ev_list:
                    counts[ev.evidence_type] = counts.get(ev.evidence_type, 0) + 1
                r["evidence_counts"] = counts
                results.append(ReleaseResponse(**r))
        return results

    def update_release_status(self, release_id: str, decision: str, trust_score: Optional[float], assessment_id: str) -> Optional[ReleaseResponse]:
        releases = self._read_data("releases")
        for r in releases:
            if r["release_id"] == release_id:
                r["latest_decision"] = decision
                r["latest_trust_score"] = trust_score
                r["latest_assessment_id"] = assessment_id
                r["updated_at"] = utc_now_iso()
                self._write_data("releases", releases)
                return ReleaseResponse(**r)
        return None

    # ------------------ Evidence ------------------
    def save_evidence(self, evidence: EvidenceEnvelope) -> EvidenceEnvelope:
        ev_list = self._read_data("evidence")
        ev_list.append(evidence.model_dump())
        self._write_data("evidence", ev_list)
        return evidence

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceEnvelope]:
        ev_list = self._read_data("evidence")
        for ev in ev_list:
            if ev["evidence_id"] == evidence_id:
                return EvidenceEnvelope(**ev)
        return None

    def list_evidence_for_release(self, release_id: str) -> List[EvidenceEnvelope]:
        ev_list = self._read_data("evidence")
        matched = [EvidenceEnvelope(**ev) for ev in ev_list if ev["release_id"] == release_id]
        return sorted(matched, key=lambda x: x.received_at)

    def is_evidence_duplicate(self, release_id: str, evidence_type: str, content_sha256: str) -> bool:
        ev_list = self._read_data("evidence")
        for ev in ev_list:
            if (
                ev["release_id"] == release_id
                and ev["evidence_type"] == evidence_type
                and ev["content_sha256"] == content_sha256
            ):
                return True
        return False

    # ------------------ Assessments ------------------
    def save_assessment(self, assessment: AssessmentRecord) -> AssessmentRecord:
        assessments = self._read_data("assessments")
        assessments.append(assessment.model_dump())
        self._write_data("assessments", assessments)
        return assessment

    def get_latest_assessment(self, release_id: str) -> Optional[AssessmentRecord]:
        history = self.list_assessments(release_id)
        if not history:
            return None
        return history[-1]

    def list_assessments(self, release_id: str) -> List[AssessmentRecord]:
        assessments = self._read_data("assessments")
        matched = [AssessmentRecord(**a) for a in assessments if a["release_id"] == release_id]
        return sorted(matched, key=lambda x: x.assessment_version)

    # ------------------ Audit Events ------------------
    def record_audit_event(self, event: AuditEvent) -> AuditEvent:
        events = self._read_data("audit")
        events.append(event.model_dump())
        self._write_data("audit", events)
        return event

    def list_audit_events(self, project_id: Optional[str] = None, release_id: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
        events = self._read_data("audit")
        filtered = []
        for e in events:
            if project_id and e.get("project_id") != project_id:
                continue
            if release_id and e.get("release_id") != release_id:
                continue
            filtered.append(AuditEvent(**e))
        # Sort descending by timestamp
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered[:limit]

    # ------------------ Users ------------------
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        users = self._read_data("users")
        for u in users:
            if u["email"].lower() == email.lower():
                return u
        return None

    def save_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        users = self._read_data("users")
        for idx, u in enumerate(users):
            if u["email"].lower() == user_data["email"].lower():
                users[idx] = user_data
                self._write_data("users", users)
                return user_data
        users.append(user_data)
        self._write_data("users", users)
        return user_data

    # ------------------ Artifacts Storage ------------------
    def store_artifact(self, key: str, file_obj: BinaryIO) -> str:
        safe_rel_path = key.replace("/", os.sep)
        full_path = os.path.join(self.artifacts_dir, safe_rel_path)
        validated_path = validate_safe_path(self.artifacts_dir, full_path)
        os.makedirs(os.path.dirname(validated_path), exist_ok=True)
        with open(validated_path, "wb") as f:
            while chunk := file_obj.read(65536):
                f.write(chunk)
        return validated_path

    def get_artifact_bytes(self, key: str) -> Optional[bytes]:
        safe_rel_path = key.replace("/", os.sep)
        full_path = os.path.join(self.artifacts_dir, safe_rel_path)
        try:
            validated_path = validate_safe_path(self.artifacts_dir, full_path)
            if os.path.exists(validated_path):
                with open(validated_path, "rb") as f:
                    return f.read()
        except Exception:
            return None
        return None
