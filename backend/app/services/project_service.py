from typing import List, Optional
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.project import ProjectCreate, ProjectResponse, ProjectPolicy

class ProjectService:
    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def create_project(self, project: ProjectCreate, creator: str) -> ProjectResponse:
        return self.repo.create_project(project, creator)

    def get_project(self, project_id: str) -> Optional[ProjectResponse]:
        return self.repo.get_project(project_id)

    def list_projects(self) -> List[ProjectResponse]:
        return self.repo.list_projects()

    def update_policy(self, project_id: str, policy: ProjectPolicy) -> Optional[ProjectResponse]:
        return self.repo.update_project_policy(project_id, policy)
