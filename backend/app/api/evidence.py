from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.schemas.evidence import EvidenceSubmission, EvidenceEnvelope, EvidenceList
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.assessment_service import AssessmentService
from backend.app.dependencies import get_repository, get_current_user, require_roles
from backend.app.repositories.base import BaseRepository

router = APIRouter(prefix="/releases", tags=["Evidence"])

@router.post("/{release_id}/evidence", status_code=status.HTTP_201_CREATED)
async def submit_evidence(
    release_id: str,
    submission: EvidenceSubmission,
    repo: BaseRepository = Depends(get_repository),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "DEVELOPER"]))
):
    """
    Submit release evidence envelope (SBOM, Provenance, Vulnerability Scan, Tests).
    Validates schema, deduplicates submissions, persists state, triggers ECTE reassessment,
    and broadcasts state change to the live dashboard.
    """
    ev_service = EvidenceService(repo)
    envelope, is_duplicate = ev_service.ingest_evidence(
        release_id=release_id,
        submission=submission,
        actor=user["email"]
    )

    if is_duplicate:
        # Return existing without redundant reassessment
        return {
            "message": "Duplicate evidence payload detected; existing envelope retained.",
            "is_duplicate": True,
            "evidence": envelope
        }

    # Broadcast evidence submission event
    from backend.app.services.event_service import broadcaster
    import uuid
    from backend.app.utils.timestamps import utc_now_iso

    now = utc_now_iso()
    release = repo.get_release(release_id)
    project_id = release.project_id if release else "unknown"
    ev_type = envelope.evidence_type
    
    specific_type = "EVIDENCE_SUBMITTED"
    if ev_type == "artifact_integrity":
        specific_type = "ARTIFACT_VERIFIED"
    elif ev_type == "vulnerability_scan":
        specific_type = "VULNERABILITY_SCAN_COMPLETED"
    elif ev_type == "provenance":
        specific_type = "PROVENANCE_VERIFIED"
    elif ev_type == "test_results":
        specific_type = "TEST_RESULTS_RECEIVED"

    is_demo = "demo" in user["email"].lower() or "scenario" in user["email"].lower()
    
    await broadcaster.broadcast({
        "event_id": f"evt-{uuid.uuid4().hex[:8]}",
        "event_type": specific_type,
        "type": specific_type,
        "occurred_at": now,
        "timestamp": now,
        "release_id": release_id,
        "project_id": project_id,
        "correlation_id": envelope.correlation_id,
        "actor": user["email"],
        "reason_codes": [f"EVIDENCE_TYPE_{ev_type.upper()}"],
        "summary": f"Evidence '{ev_type}' (v{envelope.evidence_version}) verified and ingested for release {release_id}.",
        "is_demo": is_demo,
        "details": {
            "evidence_id": envelope.evidence_id,
            "evidence_type": ev_type,
            "content_sha256": envelope.content_sha256
        }
    })

    # Automatically trigger ECTE reassessment
    asm_service = AssessmentService(repo)
    assessment = await asm_service.trigger_reassessment(
        release_id=release_id,
        actor=user["email"]
    )

    return {
        "message": "Evidence ingested and reassessment completed successfully.",
        "is_duplicate": False,
        "evidence": envelope,
        "assessment_version": assessment.assessment_version,
        "latest_decision": assessment.decision,
        "latest_trust_score": assessment.trust_score
    }

@router.get("/{release_id}/evidence", response_model=EvidenceList)
def get_release_evidence(
    release_id: str,
    repo: BaseRepository = Depends(get_repository)
):
    ev_service = EvidenceService(repo)
    items = ev_service.list_evidence(release_id=release_id)
    return EvidenceList(items=items, total=len(items))
