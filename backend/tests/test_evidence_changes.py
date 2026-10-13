import pytest
from backend.app.repositories.local_repository import LocalRepository
from backend.app.schemas.project import ProjectCreate, ProjectPolicy
from backend.app.schemas.release import ReleaseCreate, ArtifactDescriptor, EvidenceRequirements
from backend.app.schemas.evidence import EvidenceSubmission
from backend.app.services.project_service import ProjectService
from backend.app.services.release_service import ReleaseService
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.assessment_service import AssessmentService

@pytest.mark.asyncio
async def test_evidence_change_detection_and_reassessment(tmp_path):
    repo = LocalRepository(storage_dir=str(tmp_path))
    proj_srv = ProjectService(repo)
    rel_srv = ReleaseService(repo)
    ev_srv = EvidenceService(repo)
    asm_srv = AssessmentService(repo)

    # 1. Create Project & Release
    proj_srv.create_project(
        ProjectCreate(project_id="p1", name="Proj 1", policy=ProjectPolicy(block_on_critical_vuln=True)),
        creator="admin"
    )
    rel_srv.create_release(
        ReleaseCreate(
            project_id="p1",
            release_id="r1",
            version="1.0.0",
            source_commit="commit1",
            artifact=ArtifactDescriptor(filename="app.zip", expected_sha256="aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899")
        ),
        creator="admin"
    )

    # 2. Ingest initial clean evidence
    ev_srv.ingest_evidence(
        release_id="r1",
        submission=EvidenceSubmission(
            evidence_type="artifact_integrity",
            payload={"filename": "app.zip", "calculated_sha256": "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899", "expected_sha256": "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899", "matches": True, "byte_size": 100}
        )
    )
    ev_srv.ingest_evidence(
        release_id="r1",
        submission=EvidenceSubmission(
            evidence_type="vulnerability_scan",
            payload={"scanner_name": "OSV", "scan_timestamp": "2026-10-10T12:00:00Z", "total_findings": 0, "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0, "findings": []}
        )
    )

    asm1 = await asm_srv.trigger_reassessment("r1")
    assert asm1.assessment_version == 1

    # 3. New Critical Vulnerability Evidence Arrives
    ev_srv.ingest_evidence(
        release_id="r1",
        submission=EvidenceSubmission(
            evidence_type="vulnerability_scan",
            payload={
                "scanner_name": "OSV",
                "scan_timestamp": "2026-10-10T12:30:00Z",
                "total_findings": 1,
                "critical_count": 1,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "findings": [{"id": "CVE-CRIT-999", "package": "vuln-pkg", "version": "1.0", "severity": "CRITICAL"}]
            }
        )
    )

    asm2 = await asm_srv.trigger_reassessment("r1")
    assert asm2.assessment_version == 2
    assert asm2.decision == "BLOCK"
    assert asm2.previous_assessment_id == asm1.assessment_id
    assert any("CRITICAL" in r for r in asm2.blocking_reasons)

    # Verify audit event recorded the change
    audits = repo.list_audit_events(release_id="r1")
    assert len(audits) >= 2
    latest_audit = audits[0]
    assert latest_audit.new_assessment_version == 2
    assert "CRITICAL_VULNERABILITY_DETECTED" in latest_audit.reason_codes
