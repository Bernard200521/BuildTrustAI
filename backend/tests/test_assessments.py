import pytest
from backend.app.repositories.local_repository import LocalRepository
from backend.app.schemas.project import ProjectCreate
from backend.app.schemas.release import ReleaseCreate, ArtifactDescriptor
from backend.app.services.project_service import ProjectService
from backend.app.services.release_service import ReleaseService
from backend.app.services.assessment_service import AssessmentService

@pytest.mark.asyncio
async def test_assessment_history_retention(tmp_path):
    repo = LocalRepository(storage_dir=str(tmp_path))
    proj_srv = ProjectService(repo)
    rel_srv = ReleaseService(repo)
    asm_srv = AssessmentService(repo)

    proj_srv.create_project(ProjectCreate(project_id="hp", name="Hist Proj"), creator="admin")
    rel_srv.create_release(
        ReleaseCreate(
            project_id="hp", release_id="hr1", version="1.0.0", source_commit="commit1234",
            artifact=ArtifactDescriptor(filename="a.zip", expected_sha256="1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff")
        ),
        creator="admin"
    )

    asm1 = await asm_srv.trigger_reassessment("hr1")
    asm2 = await asm_srv.trigger_reassessment("hr1")
    asm3 = await asm_srv.trigger_reassessment("hr1")

    history = asm_srv.list_history("hr1")
    assert len(history) == 3
    assert [a.assessment_version for a in history] == [1, 2, 3]
