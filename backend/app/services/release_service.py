import uuid
from typing import List, Optional
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.release import ReleaseCreate, ReleaseResponse
from backend.app.schemas.audit import AuditEvent
from backend.app.utils.timestamps import utc_now_iso

class ReleaseService:
    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def create_release(self, release: ReleaseCreate, creator: str) -> ReleaseResponse:
        # Verify project exists
        project = self.repo.get_project(release.project_id)
        if not project:
            raise ValueError(f"Project with ID '{release.project_id}' does not exist.")

        created = self.repo.create_release(release, creator)

        # Audit event
        event = AuditEvent(
            event_id=f"evt-{uuid.uuid4().hex[:8]}",
            event_type="RELEASE_CREATED",
            project_id=release.project_id,
            release_id=release.release_id,
            timestamp=utc_now_iso(),
            actor=creator,
            details={
                "version": release.version,
                "commit": release.source_commit,
                "environment": release.environment
            }
        )
        self.repo.record_audit_event(event)
        return created

    def get_release(self, release_id: str) -> Optional[ReleaseResponse]:
        return self.repo.get_release(release_id)

    def list_releases(self, project_id: Optional[str] = None) -> List[ReleaseResponse]:
        return self.repo.list_releases(project_id)
