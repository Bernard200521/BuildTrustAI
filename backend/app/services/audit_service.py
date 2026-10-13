from typing import List, Optional
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.audit import AuditEvent

class AuditService:
    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def list_events(self, project_id: Optional[str] = None, release_id: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
        return self.repo.list_audit_events(project_id=project_id, release_id=release_id, limit=limit)
