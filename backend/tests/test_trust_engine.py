from backend.app.schemas.project import ProjectPolicy
from backend.app.schemas.release import ReleaseResponse, ArtifactDescriptor, EvidenceRequirements
from backend.app.schemas.evidence import EvidenceEnvelope
from backend.app.services.trust_engine import TrustEngine

def test_trust_engine_scoring_formula():
    engine = TrustEngine()
    policy = ProjectPolicy(approval_threshold=85.0)
    release = ReleaseResponse(
        release_id="rel-test-01",
        project_id="test-proj",
        version="1.0.0",
        source_commit="commit123",
        artifact=ArtifactDescriptor(
            filename="app.zip",
            expected_sha256="aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899"
        ),
        evidence_requirements=EvidenceRequirements(
            sbom_required=True,
            provenance_required=True,
            tests_required=True,
            dependency_scan_required=True
        ),
        policy_version="1.0",
        environment="staging",
        created_at="2026-10-10T12:00:00Z",
        updated_at="2026-10-10T12:00:00Z",
        created_by="tester"
    )

    ev_list = [
        EvidenceEnvelope(
            evidence_id="ev-1", project_id="test-proj", release_id="rel-test-01",
            evidence_type="artifact_integrity", source="verifier", observed_at="2026-10-10T12:00:00Z",
            received_at="2026-10-10T12:00:00Z",
            payload={"matches": True, "calculated_sha256": release.artifact.expected_sha256},
            content_sha256="1111111111111111111111111111111111111111111111111111111111111111", correlation_id="c1"
        ),
        EvidenceEnvelope(
            evidence_id="ev-2", project_id="test-proj", release_id="rel-test-01",
            evidence_type="vulnerability_scan", source="scanner", observed_at="2026-10-10T12:00:00Z",
            received_at="2026-10-10T12:00:00Z",
            payload={"critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0, "total_findings": 0},
            content_sha256="2222222222222222222222222222222222222222222222222222222222222222", correlation_id="c2"
        ),
        EvidenceEnvelope(
            evidence_id="ev-3", project_id="test-proj", release_id="rel-test-01",
            evidence_type="provenance", source="slsa", observed_at="2026-10-10T12:00:00Z",
            received_at="2026-10-10T12:00:00Z",
            payload={"builder_id": "builder", "source_revision": "commit123", "artifact_digest": release.artifact.expected_sha256, "slsa_level": "SLSA_BUILD_LEVEL_2", "cosign_verified": "VERIFIED"},
            content_sha256="3333333333333333333333333333333333333333333333333333333333333333", correlation_id="c3"
        ),
        EvidenceEnvelope(
            evidence_id="ev-4", project_id="test-proj", release_id="rel-test-01",
            evidence_type="test_results", source="pytest", observed_at="2026-10-10T12:00:00Z",
            received_at="2026-10-10T12:00:00Z",
            payload={"total_tests": 10, "passed": 10, "failed": 0, "mandatory_tests_passed": True},
            content_sha256="4444444444444444444444444444444444444444444444444444444444444444", correlation_id="c4"
        ),
        EvidenceEnvelope(
            evidence_id="ev-5", project_id="test-proj", release_id="rel-test-01",
            evidence_type="sbom", source="cdx", observed_at="2026-10-10T12:00:00Z",
            received_at="2026-10-10T12:00:00Z",
            payload={"component_count": 5, "components": []},
            content_sha256="5555555555555555555555555555555555555555555555555555555555555555", correlation_id="c5"
        )
    ]

    record, audit = engine.assess_release(release, policy, ev_list)
    assert record.trust_score == 100.0
    assert record.decision == "APPROVE"
    assert audit is not None
