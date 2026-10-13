from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.schemas.assessment import AssessmentRecord, AssessmentHistory
from backend.app.services.assessment_service import AssessmentService
from backend.app.dependencies import get_repository, get_current_user, require_roles
from backend.app.repositories.base import BaseRepository

router = APIRouter(prefix="/releases", tags=["Assessments"])

@router.post("/{release_id}/assessments", response_model=AssessmentRecord)
async def trigger_release_reassessment(
    release_id: str,
    repo: BaseRepository = Depends(get_repository),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "DEVELOPER"]))
):
    service = AssessmentService(repo)
    return await service.trigger_reassessment(release_id=release_id, actor=user["email"])

@router.get("/{release_id}/assessments/latest", response_model=AssessmentRecord)
def get_latest_assessment(
    release_id: str,
    repo: BaseRepository = Depends(get_repository)
):
    service = AssessmentService(repo)
    asm = service.get_latest_assessment(release_id)
    if not asm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No assessment found for release '{release_id}'.")
    return asm

@router.get("/{release_id}/assessments/history", response_model=AssessmentHistory)
def get_assessment_history(
    release_id: str,
    repo: BaseRepository = Depends(get_repository)
):
    service = AssessmentService(repo)
    items = service.list_history(release_id)
    return AssessmentHistory(release_id=release_id, items=items, total=len(items))
