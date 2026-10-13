import json
import os
import hashlib
from typing import Dict, Any, List, Optional
from backend.app.schemas.project import ProjectCreate, ProjectPolicy
from backend.app.schemas.release import ReleaseCreate, ArtifactDescriptor, EvidenceRequirements
from backend.app.schemas.evidence import EvidenceSubmission
from backend.app.repositories.base import BaseRepository
from backend.app.services.project_service import ProjectService
from backend.app.services.release_service import ReleaseService
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.assessment_service import AssessmentService
from backend.app.services.event_service import broadcaster
from backend.app.utils.timestamps import utc_now_iso

class ScenarioGenerator:
    """
    Executes reproducible demonstration scenarios to test release verification workflows.
    All scenarios persist real evidence records, invoke authoritative ECTE trust assessments,
    and broadcast live SSE events to connected dashboards.
    """

    def __init__(self, repo: BaseRepository):
        self.repo = repo
        self.proj_service = ProjectService(repo)
        self.rel_service = ReleaseService(repo)
        self.ev_service = EvidenceService(repo)
        self.asm_service = AssessmentService(repo)

    def _ensure_payment_project_and_release(self, release_id: str = "rel-payment-1.0.0") -> str:
        project_id = "payment-gateway"
        if not self.repo.get_project(project_id):
            self.proj_service.create_project(
                ProjectCreate(
                    project_id=project_id,
                    name="Global Payment Gateway",
                    description="PCI-DSS compliant payment processing service",
                    policy=ProjectPolicy(
                        approval_threshold=85.0,
                        review_threshold=60.0,
                        block_on_critical_vuln=True,
                        block_on_hash_mismatch=True,
                        require_provenance=True,
                        require_tests=True,
                        require_sbom=True,
                        require_dependency_scan=True
                    )
                ),
                creator="lead-secops@buildtrust.ai"
            )

        artifact_path = "sample_data/payment-service-1.0.0.zip"
        if os.path.exists(artifact_path):
            with open(artifact_path, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest().lower()
                size = os.path.getsize(artifact_path)
        else:
            sha256 = "ae4cb295b8a6d34680bede3714ee8ea7f69d65e148c7f7adedd56ac866a4abad"
            size = 2048

        if not self.repo.get_release(release_id):
            self.rel_service.create_release(
                ReleaseCreate(
                    project_id=project_id,
                    release_id=release_id,
                    version="1.0.0",
                    source_commit="a1b2c3d4e5f67890",
                    artifact=ArtifactDescriptor(
                        filename="payment-service-1.0.0.zip",
                        expected_sha256=sha256,
                        size_bytes=size
                    ),
                    evidence_requirements=EvidenceRequirements(
                        sbom_required=True,
                        provenance_required=True,
                        tests_required=True,
                        dependency_scan_required=True
                    ),
                    environment="staging"
                ),
                creator="lead-dev@buildtrust.ai"
            )
        return sha256

    async def run_scenario_a_trusted_release(self, release_id: str = "rel-payment-1.0.0") -> Dict[str, Any]:
        """
        Scenario A: Trusted Release Candidate.
        Submits complete, clean evidence (valid artifact hash, clean SBOM, clean vulnerability scan,
        valid build provenance, passing security tests). Result: Decision APPROVE (Trust Score >= 85).
        """
        sha256 = self._ensure_payment_project_and_release(release_id)

        # 1. Artifact Integrity
        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="artifact_integrity",
                source="artifact_verifier",
                payload={
                    "filename": "payment-service-1.0.0.zip",
                    "calculated_sha256": sha256,
                    "expected_sha256": sha256,
                    "matches": True,
                    "byte_size": 309
                }
            ),
            actor="scenario_runner"
        )

        # 2. Clean SBOM
        with open("sample_data/sbom/cyclonedx-clean.json", "r") as f:
            sbom_data = json.load(f)
        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="sbom",
                source="cyclonedx-cli",
                payload={
                    "format": "CycloneDX",
                    "spec_version": "1.5",
                    "component_count": len(sbom_data.get("components", [])),
                    "components": sbom_data.get("components", []),
                    "duplicate_components": [],
                    "has_signature": True
                }
            ),
            actor="scenario_runner"
        )

        # 3. Clean Vulnerability Scan
        with open("sample_data/vulnerability_reports/vuln-clean.json", "r") as f:
            vuln_data = json.load(f)
        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="vulnerability_scan",
                source="osv-scanner",
                payload=vuln_data
            ),
            actor="scenario_runner"
        )

        # 4. Valid Provenance
        with open("sample_data/provenance/provenance-valid.json", "r") as f:
            prov_data = json.load(f)
        prov_data["artifact_digest"] = sha256
        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="provenance",
                source="slsa-verifier",
                payload=prov_data
            ),
            actor="scenario_runner"
        )

        # 5. Passing Security Tests
        with open("sample_data/test_results/tests-passed.json", "r") as f:
            test_data = json.load(f)
        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="test_results",
                source="pytest-runner",
                payload=test_data
            ),
            actor="scenario_runner"
        )

        asm = await self.asm_service.trigger_reassessment(release_id=release_id, actor="Scenario_A")
        return {
            "scenario": "A_TRUSTED_RELEASE",
            "release_id": release_id,
            "decision": asm.decision,
            "trust_score": asm.trust_score,
            "assessment_version": asm.assessment_version,
            "blocking_reasons": asm.blocking_reasons,
            "is_demo": True
        }

    async def run_scenario_b_tampering(self, release_id: str = "rel-payment-1.0.0") -> Dict[str, Any]:
        """
        Scenario B: Artifact Tampering.
        Submits an artifact hash mismatch. Deterministic policy triggers immediate BLOCK
        regardless of trust score.
        """
        self._ensure_payment_project_and_release(release_id)
        expected_sha = "ae4cb295b8a6d34680bede3714ee8ea7f69d65e148c7f7adedd56ac866a4abad"
        tampered_sha = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"

        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="artifact_integrity",
                source="artifact_verifier",
                payload={
                    "filename": "payment-service-1.0.0.zip",
                    "calculated_sha256": tampered_sha,
                    "expected_sha256": expected_sha,
                    "matches": False,
                    "byte_size": 4096
                }
            ),
            actor="scenario_runner"
        )

        asm = await self.asm_service.trigger_reassessment(release_id=release_id, actor="Scenario_B")
        return {
            "scenario": "B_ARTIFACT_TAMPERING",
            "release_id": release_id,
            "decision": asm.decision,
            "trust_score": asm.trust_score,
            "assessment_version": asm.assessment_version,
            "blocking_reasons": asm.blocking_reasons,
            "is_demo": True
        }

    async def run_scenario_c_vulnerability(self, release_id: str = "rel-payment-1.0.0") -> Dict[str, Any]:
        """
        Scenario C: Vulnerability Discovered.
        Injects a verified critical Log4Shell CVE finding. Reassessment triggers zero-tolerance
        security policy BLOCK.
        """
        self._ensure_payment_project_and_release(release_id)
        with open("sample_data/vulnerability_reports/vuln-critical.json", "r") as f:
            vuln_data = json.load(f)

        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="vulnerability_scan",
                source="osv-continuous-monitor",
                payload=vuln_data
            ),
            actor="scenario_runner"
        )

        asm = await self.asm_service.trigger_reassessment(release_id=release_id, actor="Scenario_C")
        return {
            "scenario": "C_VULNERABILITY_DISCOVERED",
            "release_id": release_id,
            "decision": asm.decision,
            "trust_score": asm.trust_score,
            "assessment_version": asm.assessment_version,
            "blocking_reasons": asm.blocking_reasons,
            "is_demo": True
        }

    async def run_scenario_d_missing_provenance(self, release_id: str = "rel-payment-1.0.0") -> Dict[str, Any]:
        """
        Scenario D: Missing Provenance.
        Submits valid artifact and tests but lacks required build provenance attestation.
        Evaluates to INSUFFICIENT_EVIDENCE.
        """
        sha256 = self._ensure_payment_project_and_release(release_id)

        # Submit valid artifact
        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="artifact_integrity",
                source="artifact_verifier",
                payload={
                    "filename": "payment-service-1.0.0.zip",
                    "calculated_sha256": sha256,
                    "expected_sha256": sha256,
                    "matches": True,
                    "byte_size": 309
                }
            ),
            actor="scenario_runner"
        )

        # Submit clean vulns
        with open("sample_data/vulnerability_reports/vuln-clean.json", "r") as f:
            vuln_data = json.load(f)
        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="vulnerability_scan",
                source="osv-scanner",
                payload=vuln_data
            ),
            actor="scenario_runner"
        )

        asm = await self.asm_service.trigger_reassessment(release_id=release_id, actor="Scenario_D")
        return {
            "scenario": "D_MISSING_PROVENANCE",
            "release_id": release_id,
            "decision": asm.decision,
            "trust_score": asm.trust_score,
            "assessment_version": asm.assessment_version,
            "blocking_reasons": asm.blocking_reasons,
            "is_demo": True
        }

    async def run_scenario_e_test_failure(self, release_id: str = "rel-payment-1.0.0") -> Dict[str, Any]:
        """
        Scenario E: Test Failure.
        Submits failing mandatory security regression test results.
        Mandatory test failure rule triggers deterministic BLOCK.
        """
        self._ensure_payment_project_and_release(release_id)
        with open("sample_data/test_results/tests-failed.json", "r") as f:
            test_data = json.load(f)

        self.ev_service.ingest_evidence(
            release_id=release_id,
            submission=EvidenceSubmission(
                evidence_type="test_results",
                source="pytest-runner",
                payload=test_data
            ),
            actor="scenario_runner"
        )

        asm = await self.asm_service.trigger_reassessment(release_id=release_id, actor="Scenario_E")
        return {
            "scenario": "E_TEST_FAILURE",
            "release_id": release_id,
            "decision": asm.decision,
            "trust_score": asm.trust_score,
            "assessment_version": asm.assessment_version,
            "blocking_reasons": asm.blocking_reasons,
            "is_demo": True
        }
