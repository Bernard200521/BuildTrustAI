import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath("."))

from backend.app.dependencies import get_repository
from backend.app.simulator.scenario_generator import ScenarioGenerator
from backend.app.schemas.project import ProjectCreate, ProjectPolicy
from backend.app.schemas.release import ReleaseCreate, ArtifactDescriptor, EvidenceRequirements
from backend.app.schemas.evidence import EvidenceSubmission
from backend.app.services.project_service import ProjectService
from backend.app.services.release_service import ReleaseService
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.assessment_service import AssessmentService

async def main():
    print("Initializing repository for demo seeding...")
    repo = get_repository()
    scenario = ScenarioGenerator(repo)
    proj_srv = ProjectService(repo)
    rel_srv = ReleaseService(repo)
    ev_srv = EvidenceService(repo)
    asm_srv = AssessmentService(repo)

    # 1. Seed Scenario A (Trusted Release)
    print("Seeding Scenario A (Trusted Payment Gateway)...")
    res_a = await scenario.run_scenario_a_trusted_release()
    print(f" -> Scenario A: {res_a['decision']} (Score: {res_a['trust_score']})")

    # 2. Seed Scenario C (Tampered Release)
    print("Seeding Scenario C (Tampered Auth Broker)...")
    res_c = await scenario.run_scenario_c_tampering()
    print(f" -> Scenario C: {res_c['decision']} (Score: {res_c['trust_score']})")

    # 3. Seed Analytics Pipeline (Missing Provenance / Incomplete Evidence)
    print("Seeding Scenario D (Analytics Pipeline - Incomplete Evidence)...")
    proj_d = "analytics-pipeline"
    if not repo.get_project(proj_d):
        proj_srv.create_project(
            ProjectCreate(
                project_id=proj_d,
                name="Data Engineering Analytics Pipeline",
                description="Distributed stream analytics engine"
            ),
            creator="data-eng@buildtrust.ai"
        )
    rel_d = "rel-analytics-3.0.0"
    if not repo.get_release(rel_d):
        rel_srv.create_release(
            ReleaseCreate(
                project_id=proj_d,
                release_id=rel_d,
                version="3.0.0",
                source_commit="commit-analytics-777",
                artifact=ArtifactDescriptor(
                    filename="analytics-engine.jar",
                    expected_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
                ),
                evidence_requirements=EvidenceRequirements(
                    provenance_required=True,
                    sbom_required=True
                )
            ),
            creator="data-eng@buildtrust.ai"
        )
    # Submit only test results, no provenance or sbom
    ev_srv.ingest_evidence(
        release_id=rel_d,
        submission=EvidenceSubmission(
            evidence_type="test_results",
            source="junit-runner",
            payload={"total_tests": 120, "passed": 120, "failed": 0, "mandatory_tests_passed": True}
        )
    )
    asm_d = await asm_srv.trigger_reassessment(release_id=rel_d, actor="Demo_Seeder")
    print(f" -> Scenario D: {asm_d.decision} (Score: {asm_d.trust_score})")

    # 4. Seed Scenario E (AI Anomaly Release)
    print("Seeding Scenario E (Risk Scoring Worker - AI Anomaly Flagged)...")
    proj_e = "risk-worker"
    if not repo.get_project(proj_e):
        proj_srv.create_project(
            ProjectCreate(
                project_id=proj_e,
                name="Risk Scoring Worker",
                description="Real-time transaction risk scoring microservice"
            ),
            creator="ai-eng@buildtrust.ai"
        )
    rel_e = "rel-worker-1.5.0"
    w_hash = "abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd"
    if not repo.get_release(rel_e):
        rel_srv.create_release(
            ReleaseCreate(
                project_id=proj_e,
                release_id=rel_e,
                version="1.5.0",
                source_commit="commit-worker-888",
                artifact=ArtifactDescriptor(
                    filename="risk-worker.tar.gz",
                    expected_sha256=w_hash
                )
            ),
            creator="ai-eng@buildtrust.ai"
        )
    # Valid integrity
    ev_srv.ingest_evidence(
        release_id=rel_e,
        submission=EvidenceSubmission(
            evidence_type="artifact_integrity",
            payload={"filename": "risk-worker.tar.gz", "calculated_sha256": w_hash, "expected_sha256": w_hash, "matches": True, "byte_size": 10240}
        )
    )
    # Provenance with low SLSA level and partial notes
    ev_srv.ingest_evidence(
        release_id=rel_e,
        submission=EvidenceSubmission(
            evidence_type="provenance",
            payload={"builder_id": "generic-ad-hoc-agent", "source_revision": "commit-worker-888", "artifact_digest": w_hash, "slsa_level": "SLSA_BUILD_LEVEL_1", "cosign_verified": "NOT_PERFORMED"}
        )
    )
    # High volume of moderate vulnerabilities causing feature space outlier
    ev_srv.ingest_evidence(
        release_id=rel_e,
        submission=EvidenceSubmission(
            evidence_type="vulnerability_scan",
            payload={
                "scanner_name": "OSV-Scanner",
                "scan_timestamp": "2026-10-10T12:30:00Z",
                "total_findings": 6,
                "critical_count": 0,
                "high_count": 2,
                "medium_count": 4,
                "low_count": 0,
                "findings": [
                    {"id": f"CVE-2026-{1000+i}", "package": f"dep-{i}", "version": "1.0", "severity": "MEDIUM", "cvss_score": 5.5, "summary": "Moderate risk"} for i in range(4)
                ] + [
                    {"id": f"CVE-2026-900{i}", "package": f"sec-lib-{i}", "version": "2.0", "severity": "HIGH", "cvss_score": 7.8, "summary": "High risk advisory"} for i in range(2)
                ]
            }
        )
    )
    asm_e = await asm_srv.trigger_reassessment(release_id=rel_e, actor="Demo_Seeder")
    print(f" -> Scenario E: {asm_e.decision} (Score: {asm_e.trust_score}, AI Anomaly: {asm_e.ai_anomaly.anomaly_detected if asm_e.ai_anomaly else 'N/A'})")

    print("\nDemonstration environment successfully seeded!")

if __name__ == "__main__":
    asyncio.run(main())
