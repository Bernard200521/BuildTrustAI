from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.schemas.project import ProjectCreate, ProjectResponse, ProjectList, ProjectPolicy
from backend.app.schemas.release import ReleaseCreate, ReleaseResponse, ReleaseList
from backend.app.services.project_service import ProjectService
from backend.app.services.release_service import ReleaseService
from backend.app.dependencies import get_repository, get_current_user, require_roles
from backend.app.repositories.base import BaseRepository

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    repo: BaseRepository = Depends(get_repository),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "DEVELOPER"]))
):
    service = ProjectService(repo)
    try:
        return service.create_project(project, creator=user["email"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.get("", response_model=ProjectList)
def list_projects(
    repo: BaseRepository = Depends(get_repository)
):
    service = ProjectService(repo)
    items = service.list_projects()
    return ProjectList(items=items, total=len(items))

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    repo: BaseRepository = Depends(get_repository)
):
    service = ProjectService(repo)
    proj = service.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
    return proj

@router.put("/{project_id}/policy", response_model=ProjectResponse)
def update_project_policy(
    project_id: str,
    policy: ProjectPolicy,
    repo: BaseRepository = Depends(get_repository),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"]))
):
    service = ProjectService(repo)
    updated = service.update_policy(project_id, policy)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
    return updated

@router.post("/{project_id}/releases", response_model=ReleaseResponse, status_code=status.HTTP_201_CREATED)
def create_release_for_project(
    project_id: str,
    release_in: ReleaseCreate,
    repo: BaseRepository = Depends(get_repository),
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "DEVELOPER"]))
):
    if release_in.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id in path does not match payload.")
    service = ReleaseService(repo)
    try:
        return service.create_release(release_in, creator=user["email"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.get("/{project_id}/releases", response_model=ReleaseList)
def list_releases_for_project(
    project_id: str,
    repo: BaseRepository = Depends(get_repository)
):
    service = ReleaseService(repo)
    items = service.list_releases(project_id=project_id)
    return ReleaseList(items=items, total=len(items))
