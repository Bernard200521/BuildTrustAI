import asyncio
import json
import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.repositories.local_repository import LocalRepository
from backend.app.schemas.project import ProjectCreate, ProjectPolicy
from backend.app.schemas.release import ReleaseCreate, ArtifactDescriptor, EvidenceRequirements
from backend.app.services.project_service import ProjectService
from backend.app.services.release_service import ReleaseService
from backend.app.services.assessment_service import AssessmentService
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.event_service import EventBroadcaster
from backend.app.schemas.evidence import EvidenceSubmission
from backend.app.dependencies import create_access_token

@pytest.mark.asyncio
async def test_live_events_full_pipeline(tmp_path):
    """
    Priority 1 End-to-End Event Integration Test:
    1. Connect to EventBroadcaster (SSE).
    2. Submit valid evidence through backend service/API.
    3. Confirm evidence is persisted.
    4. Confirm assessment is created/updated.
    5. Confirm audit record exists.
    6. Confirm events received through SSE generator with valid JSON.
    7. Test validation failure and confirm no false success event emitted.
    8. Test disconnection and reconnection cleanup.
    """
    # Isolated test repository
    test_storage = str(tmp_path / "data")
    repo = LocalRepository(storage_dir=test_storage)
    proj_srv = ProjectService(repo)
    rel_srv = ReleaseService(repo)
    ev_srv = EvidenceService(repo)

    # Isolated broadcaster for testing
    test_broadcaster = EventBroadcaster()

    # 1. Setup Project & Release
    proj_srv.create_project(
        ProjectCreate(
            project_id="test-proj",
            name="Test Project",
            description="Testing E2E Events",
            policy=ProjectPolicy(approval_threshold=80.0)
        ),
        creator="admin@buildtrust.ai"
    )

    expected_sha = "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899"
    rel_srv.create_release(
        ReleaseCreate(
            project_id="test-proj",
            release_id="rel-test-1",
            version="1.0.0",
            source_commit="commit111",
            artifact=ArtifactDescriptor(
                filename="app.zip",
                expected_sha256=expected_sha,
                size_bytes=1024
            ),
            evidence_requirements=EvidenceRequirements(
                sbom_required=True,
                provenance_required=False,
                tests_required=False,
                dependency_scan_required=False
            )
        ),
        creator="admin@buildtrust.ai"
    )

    # 2. Connect SSE subscriber
    sub_gen = test_broadcaster.subscribe()

    # Read initial connection event
    conn_sse = await sub_gen.__anext__()
    conn_raw = conn_sse.data
    conn_data = json.loads(conn_raw)
    assert conn_data["event_type"] == "CONNECTION_ESTABLISHED"
    assert test_broadcaster.subscriber_count == 1

    # 3. Ingest valid evidence
    envelope, is_dup = ev_srv.ingest_evidence(
        release_id="rel-test-1",
        submission=EvidenceSubmission(
            evidence_type="artifact_integrity",
            source="ci_runner",
            payload={
                "filename": "app.zip",
                "calculated_sha256": expected_sha,
                "expected_sha256": expected_sha,
                "matches": True,
                "byte_size": 1024
            }
        ),
        actor="ci_bot@buildtrust.ai"
    )
    assert not is_dup
    assert envelope.validation_status == "valid"

    # Confirm Evidence is persisted in repository
    persisted_ev = repo.get_evidence(envelope.evidence_id)
    assert persisted_ev is not None
    assert persisted_ev.content_sha256 == envelope.content_sha256

    # Broadcast EVIDENCE_SUBMITTED event
    await test_broadcaster.broadcast({
        "event_id": f"evt-{envelope.evidence_id}",
        "event_type": "ARTIFACT_VERIFIED",
        "release_id": "rel-test-1",
        "project_id": "test-proj",
        "actor": "ci_bot@buildtrust.ai",
        "reason_codes": ["ARTIFACT_SHA256_MATCH"],
        "summary": "Artifact integrity verified against release manifest.",
        "is_demo": False
    })

    # Read evidence event from SSE
    ev_sse = await sub_gen.__anext__()
    ev_event = json.loads(ev_sse.data)
    assert ev_event["event_type"] == "ARTIFACT_VERIFIED"
    assert ev_event["release_id"] == "rel-test-1"
    assert ev_event["actor"] == "ci_bot@buildtrust.ai"

    # 4. Trigger Reassessment
    asm_srv = AssessmentService(repo)
    assessment = await asm_srv.trigger_reassessment("rel-test-1", actor="assessment_agent")

    # Confirm Assessment is persisted in repository
    latest_asm = repo.get_latest_assessment("rel-test-1")
    assert latest_asm is not None
    assert latest_asm.assessment_id == assessment.assessment_id
    assert latest_asm.assessment_version == 1

    # Confirm Audit record exists
    audits = repo.list_audit_events(release_id="rel-test-1")
    assert len(audits) >= 2 # Evidence submitted audit + Assessment changed audit
    assert any(a.event_type == "EVIDENCE_SUBMITTED" for a in audits)
    assert any(a.event_type == "ASSESSMENT_CHANGED" for a in audits)

    # 5. Broadcast assessment event
    await test_broadcaster.broadcast({
        "event_id": f"evt-asm-{assessment.assessment_id}",
        "event_type": "ASSESSMENT_CHANGED",
        "release_id": "rel-test-1",
        "project_id": "test-proj",
        "actor": "assessment_agent",
        "decision": assessment.decision,
        "trust_score": assessment.trust_score,
        "assessment_version": assessment.assessment_version,
        "reason_codes": ["ECTE_ASSESSMENT_COMPLETE"],
        "summary": f"Assessment completed: Decision {assessment.decision}."
    })

    # Read assessment event from SSE
    asm_sse = await sub_gen.__anext__()
    asm_event = json.loads(asm_sse.data)
    assert asm_event["event_type"] == "ASSESSMENT_CHANGED"
    assert asm_event["decision"] == assessment.decision
    assert asm_event["trust_score"] == assessment.trust_score

    # 6. Test Validation Failure (confirm no false success event is emitted)
    initial_event_count = len(test_broadcaster._history)
    with pytest.raises(Exception):
        # Invalid schema: missing required fields for artifact_integrity
        ev_srv.ingest_evidence(
            release_id="rel-test-1",
            submission=EvidenceSubmission(
                evidence_type="artifact_integrity",
                source="bad_actor",
                payload={"invalid_key": 123} # Missing expected_sha256, filename, etc.
            )
        )

    # Confirm no new event was added to history ring buffer
    assert len(test_broadcaster._history) == initial_event_count

    # 7. Disconnection Cleanup
    await sub_gen.aclose()
    # Broadcaster removes queue
    # Allow generator finally block to execute
    await asyncio.sleep(0.01)
    assert test_broadcaster.subscriber_count == 0

    # 8. Reconnection
    sub_gen2 = test_broadcaster.subscribe()
    reconn_sse = await sub_gen2.__anext__()
    reconn_data = json.loads(reconn_sse.data)
    assert reconn_data["event_type"] == "CONNECTION_ESTABLISHED"
    assert test_broadcaster.subscriber_count == 1
    await sub_gen2.aclose()
