from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from backend.app.dependencies import get_repository
from backend.app.repositories.base import BaseRepository
from backend.app.services.project_service import ProjectService
from backend.app.services.release_service import ReleaseService
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(repo: BaseRepository = Depends(get_repository)) -> Dict[str, Any]:
    proj_service = ProjectService(repo)
    rel_service = ReleaseService(repo)
    audit_service = AuditService(repo)

    projects = proj_service.list_projects()
    releases = rel_service.list_releases()
    recent_audits = audit_service.list_events(limit=10)

    total_projects = len(projects)
    total_releases = len(releases)

    approved = sum(1 for r in releases if r.latest_decision == "APPROVE")
    review = sum(1 for r in releases if r.latest_decision == "REVIEW")
    blocked = sum(1 for r in releases if r.latest_decision == "BLOCK")
    insufficient = sum(1 for r in releases if r.latest_decision == "INSUFFICIENT_EVIDENCE")
    pending = sum(1 for r in releases if r.latest_decision in ["PENDING_ASSESSMENT", "INSUFFICIENT_EVIDENCE"])

    scores = [r.latest_trust_score for r in releases if r.latest_trust_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    # Aggregate vulnerability findings across all releases
    crit_count = 0
    high_count = 0
    med_count = 0
    low_count = 0

    for r in releases:
        ev_list = repo.list_evidence_for_release(r.release_id)
        for ev in ev_list:
            if ev.evidence_type == "vulnerability_scan":
                crit_count += ev.payload.get("critical_count", 0)
                high_count += ev.payload.get("high_count", 0)
                med_count += ev.payload.get("medium_count", 0)
                low_count += ev.payload.get("low_count", 0)

    return {
        "metrics": {
            "total_projects": total_projects,
            "total_releases": total_releases,
            "approved_releases": approved,
            "review_releases": review,
            "blocked_releases": blocked,
            "insufficient_evidence_releases": insufficient,
            "pending_releases": pending,
            "average_trust_score": avg_score
        },
        "storage_backend": repo.__class__.__name__,
        "vulnerability_distribution": {
            "CRITICAL": crit_count,
            "HIGH": high_count,
            "MEDIUM": med_count,
            "LOW": low_count
        },
        "recent_events": [e.model_dump() for e in recent_audits],
        "recent_releases": [r.model_dump() for r in releases[:8]]
    }
