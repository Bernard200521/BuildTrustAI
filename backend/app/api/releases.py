from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from backend.app.schemas.release import ReleaseResponse, ReleaseList
from backend.app.schemas.audit import AuditList
from backend.app.schemas.evidence import EvidenceSubmission
from backend.app.services.release_service import ReleaseService
from backend.app.services.audit_service import AuditService
from backend.app.services.artifact_verifier import ArtifactVerifier
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.assessment_service import AssessmentService
from backend.app.dependencies import (
    get_repository,
    get_s3_repository,
    get_current_user,
    require_roles
)
from backend.app.repositories.base import BaseRepository
from backend.app.repositories.s3_repository import S3Repository
from backend.app.utils.validation import sanitize_filename, generate_s3_artifact_key

router = APIRouter(prefix="/releases", tags=["Releases"])

class UploadUrlRequest(BaseModel):
    filename: str

@router.get("", response_model=ReleaseList)
def list_all_releases(
    project_id: Optional[str] = None,
    repo: BaseRepository = Depends(get_repository)
):
    service = ReleaseService(repo)
    items = service.list_releases(project_id=project_id)
    return ReleaseList(items=items, total=len(items))

@router.get("/{release_id}", response_model=ReleaseResponse)
def get_release(
    release_id: str,
    repo: BaseRepository = Depends(get_repository)
):
    service = ReleaseService(repo)
    rel = service.get_release(release_id)
    if not rel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Release '{release_id}' not found.")
    return rel

@router.post("/{release_id}/artifacts/upload-url")
def request_upload_url(
    release_id: str,
    req: UploadUrlRequest,
    repo: BaseRepository = Depends(get_repository),
    s3_repo: Optional[S3Repository] = Depends(get_s3_repository),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "DEVELOPER"]))
):
    service = ReleaseService(repo)
    rel = service.get_release(release_id)
    if not rel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Release '{release_id}' not found.")

    clean_file = sanitize_filename(req.filename)
    s3_key = generate_s3_artifact_key(rel.project_id, rel.version, clean_file)

    if s3_repo:
        presigned = s3_repo.generate_presigned_upload_url(s3_key)
        return {
            "mode": "aws_s3_presigned",
            "upload_url": presigned["upload_url"],
            "s3_key": s3_key,
            "filename": clean_file
        }
    else:
        # Local direct upload endpoint
        return {
            "mode": "local_direct",
            "upload_url": f"/api/v1/releases/{release_id}/artifacts/upload",
            "key": s3_key,
            "filename": clean_file
        }

@router.post("/{release_id}/artifacts/upload")
async def upload_artifact_file(
    release_id: str,
    file: UploadFile = File(...),
    repo: BaseRepository = Depends(get_repository),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "DEVELOPER"]))
):
    """
    Direct artifact upload endpoint.
    Streams binary file, calculates actual SHA-256 digest, compares with expected hash,
    and automatically ingests an 'artifact_integrity' evidence envelope.
    """
    service = ReleaseService(repo)
    rel = service.get_release(release_id)
    if not rel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Release '{release_id}' not found.")

    clean_name = sanitize_filename(file.filename or "artifact.bin")
    key = generate_s3_artifact_key(rel.project_id, rel.version, clean_name)

    # Store artifact stream
    repo.store_artifact(key, file.file)

    # Compute actual SHA-256
    file.file.seek(0)
    verification = ArtifactVerifier.verify_file_stream(
        file_obj=file.file,
        expected_sha256=rel.artifact.expected_sha256,
        filename=clean_name
    )

    # Automatically submit as artifact_integrity evidence
    ev_service = EvidenceService(repo)
    envelope, _ = ev_service.ingest_evidence(
        release_id=release_id,
        submission=EvidenceSubmission(
            evidence_type="artifact_integrity",
            source="artifact_verifier",
            payload=verification
        ),
        actor=user["email"]
    )

    # Trigger automatic assessment
    asm_service = AssessmentService(repo)
    assessment = await asm_service.trigger_reassessment(release_id=release_id, actor=user["email"])

    return {
        "message": "Artifact uploaded and verified successfully.",
        "verification": verification,
        "evidence_id": envelope.evidence_id,
        "new_decision": assessment.decision,
        "trust_score": assessment.trust_score
    }

@router.get("/{release_id}/audit", response_model=AuditList)
def get_release_audit(
    release_id: str,
    repo: BaseRepository = Depends(get_repository)
):
    service = AuditService(repo)
    items = service.list_events(release_id=release_id)
    return AuditList(items=items, total=len(items))
