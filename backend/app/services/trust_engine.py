import uuid
from typing import List, Dict, Any, Optional, Tuple
from backend.app.schemas.project import ProjectPolicy
from backend.app.schemas.release import ReleaseResponse, ReleaseCreate
from backend.app.schemas.evidence import EvidenceEnvelope
from backend.app.schemas.assessment import (
    AssessmentRecord,
    TrustScoreBreakdown,
    ScoreComponentDetail,
    ExplanationItem,
    AIAnomalyResult
)
from backend.app.schemas.audit import AuditEvent
from backend.app.services.artifact_verifier import ArtifactVerifier
from backend.app.services.vulnerability_service import VulnerabilityService
from backend.app.services.provenance_verifier import ProvenanceVerifier
from backend.app.services.test_result_analyzer import TestResultAnalyzer
from backend.app.services.policy_engine import PolicyEngine
from backend.app.ml.feature_builder import FeatureBuilder
from backend.app.ml.inference import ModelInference
from backend.app.utils.timestamps import utc_now_iso

class TrustEngine:
    """
    Evidence-Change Trust Engine (ECTE).
    Correlates multiple streams of release evidence, detects evidence deltas,
    computes explainable composite trust scores, executes ML anomaly prioritization,
    and applies deterministic security policies.
    """

    def __init__(self, ml_inference: Optional[ModelInference] = None):
        self.ml_inference = ml_inference or ModelInference()

    def assess_release(
        self,
        release: ReleaseResponse,
        policy: ProjectPolicy,
        evidence_list: List[EvidenceEnvelope],
        previous_assessment: Optional[AssessmentRecord] = None
    ) -> Tuple[AssessmentRecord, Optional[AuditEvent]]:
        """
        Execute ECTE trust assessment workflow for a release candidate.
        Returns the new AssessmentRecord and an optional AuditEvent if state changed.
        """
        now = utc_now_iso()

        # Group latest valid evidence by evidence_type
        latest_evidence: Dict[str, EvidenceEnvelope] = {}
        for ev in evidence_list:
            if ev.validation_status in ["valid", "unverified"]:
                # Later received evidence overwrites older
                latest_evidence[ev.evidence_type] = ev

        # ---------------- 1. Component I: Artifact Integrity (Weight: 0.25) ----------------
        integrity_ev = latest_evidence.get("artifact_integrity")
        integrity_score: Optional[float] = None
        integrity_status: str = "MISSING"
        integrity_detail = "Artifact integrity evidence not submitted."
        integrity_data = None

        if integrity_ev:
            payload = integrity_ev.payload
            integrity_data = payload
            matches = payload.get("matches", False)
            if matches:
                integrity_score = 100.0
                integrity_status = "VERIFIED"
                integrity_detail = f"SHA-256 verified against expected release digest ({payload.get('calculated_sha256', '')[:12]}...)."
            else:
                integrity_score = 0.0
                integrity_status = "FAILED"
                integrity_detail = "SHA-256 digest MISMATCH with expected release digest."
        elif not release.artifact.expected_sha256:
            integrity_status = "MISSING"
            integrity_detail = "No expected SHA-256 reference provided in release manifest."

        # ---------------- 2. Component D: Dependency Security (Weight: 0.20) ----------------
        vuln_ev = latest_evidence.get("vulnerability_scan")
        sbom_ev = latest_evidence.get("sbom")
        dependency_score: Optional[float] = None
        dependency_status: str = "MISSING"
        dependency_detail = "Vulnerability scan evidence not submitted."
        vuln_data = None

        critical_c = 0
        high_c = 0
        med_c = 0
        low_c = 0

        if vuln_ev:
            vuln_data = vuln_ev.payload
            findings_raw = vuln_data.get("findings", [])
            # Recompute or use payload findings
            from backend.app.schemas.evidence import VulnFinding
            typed_findings = [VulnFinding(**f) if isinstance(f, dict) else f for f in findings_raw]
            dep_res = VulnerabilityService.calculate_dependency_score(typed_findings)
            dependency_score = dep_res["score"]
            critical_c = dep_res["critical_count"]
            high_c = dep_res["high_count"]
            med_c = dep_res["medium_count"]
            low_c = dep_res["low_count"]
            total_f = dep_res["total_findings"]

            if total_f == 0:
                dependency_status = "VERIFIED"
                dependency_detail = "No dependency vulnerabilities identified."
            elif critical_c > 0 or high_c > 0:
                dependency_status = "FAILED" if critical_c > 0 else "PARTIAL"
                dependency_detail = f"Identified {critical_c} critical, {high_c} high, {med_c} medium, {low_c} low vulnerabilities."
            else:
                dependency_status = "PARTIAL"
                dependency_detail = f"Identified {med_c} medium, {low_c} low vulnerabilities."

        # ---------------- 3. Component P: Provenance Verification (Weight: 0.20) ----------------
        prov_ev = latest_evidence.get("provenance")
        provenance_score: Optional[float] = None
        provenance_status: str = "MISSING"
        provenance_detail = "Build provenance evidence not submitted."
        prov_data = None
        prov_mandatory_passed: Optional[bool] = None

        if prov_ev:
            prov_data = prov_ev.payload
            prov_res = ProvenanceVerifier.verify_provenance(
                payload=prov_data,
                expected_commit=release.source_commit,
                expected_digest=release.artifact.expected_sha256,
                require_cosign=policy.require_cosign_verification
            )
            provenance_score = prov_res["score"]
            provenance_status = prov_res["status"]
            prov_mandatory_passed = prov_res["mandatory_passed"]
            provenance_detail = "; ".join(prov_res["notes"])

        # ---------------- 4. Component S: Test Results (Weight: 0.15) ----------------
        test_ev = latest_evidence.get("test_results")
        test_score: Optional[float] = None
        test_status: str = "MISSING"
        test_detail = "Test execution evidence not submitted."
        test_data = None
        test_mandatory_passed: Optional[bool] = None

        if test_ev:
            test_data = test_ev.payload
            test_res = TestResultAnalyzer.analyze_results(test_data)
            test_score = test_res["score"]
            test_status = test_res["status"]
            test_mandatory_passed = test_res["mandatory_passed"]
            test_detail = test_res["details"]

        # ---------------- 5. Component E: Evidence Completeness (Weight: 0.20) ----------------
        reqs = release.evidence_requirements
        required_types = []
        if reqs.sbom_required:
            required_types.append("sbom")
        if reqs.dependency_scan_required:
            required_types.append("vulnerability_scan")
        if reqs.provenance_required:
            required_types.append("provenance")
        if reqs.tests_required:
            required_types.append("test_results")
        required_types.append("artifact_integrity") # Always required

        valid_count = sum(1 for t in required_types if t in latest_evidence and latest_evidence[t].validation_status == "valid")
        total_required = len(required_types)
        completeness_pct = round((valid_count / total_required) * 100.0, 1) if total_required > 0 else 100.0
        evidence_is_complete = (valid_count == total_required)

        completeness_detail = f"{valid_count}/{total_required} required evidence envelopes verified ({completeness_pct}%)."

        # ---------------- Trust Score Baseline Calculation ----------------
        score_components = [
            ScoreComponentDetail(name="Artifact Integrity (I)", weight=0.25, score=integrity_score, status=integrity_status, details=integrity_detail), # type: ignore
            ScoreComponentDetail(name="Dependency Security (D)", weight=0.20, score=dependency_score, status=dependency_status, details=dependency_detail), # type: ignore
            ScoreComponentDetail(name="Provenance Verification (P)", weight=0.20, score=provenance_score, status=provenance_status, details=provenance_detail), # type: ignore
            ScoreComponentDetail(name="Security Tests (S)", weight=0.15, score=test_score, status=test_status, details=test_detail), # type: ignore
            ScoreComponentDetail(name="Evidence Completeness (E)", weight=0.20, score=completeness_pct, status="VERIFIED" if evidence_is_complete else "PARTIAL", details=completeness_detail) # type: ignore
        ]

        # Calculate final T = 0.25*I + 0.20*D + 0.20*P + 0.15*S + 0.20*E
        # If mandatory items are missing, final trust score reflects available components without treating missing as 100
        computed_trust_score: Optional[float] = None
        if not evidence_is_complete:
            # Partial score or None
            # Do NOT silently replace missing items with 100!
            weighted_sum = (
                (0.25 * (integrity_score or 0.0)) +
                (0.20 * (dependency_score or 0.0)) +
                (0.20 * (provenance_score or 0.0)) +
                (0.15 * (test_score or 0.0)) +
                (0.20 * completeness_pct)
            )
            computed_trust_score = round(weighted_sum, 1)
        else:
            weighted_sum = (
                (0.25 * integrity_score) +
                (0.20 * dependency_score) +
                (0.20 * provenance_score) +
                (0.15 * test_score) +
                (0.20 * completeness_pct)
            )
            computed_trust_score = round(max(0.0, min(100.0, weighted_sum)), 1)

        breakdown = TrustScoreBreakdown(
            integrity_score=integrity_score,
            dependency_score=dependency_score,
            provenance_score=provenance_score,
            test_score=test_score,
            completeness_score=completeness_pct,
            components=score_components
        )

        # ---------------- ML Anomaly Prioritization ----------------
        prev_vuln_count = 0
        if previous_assessment:
            # Check previous assessment vuln count if available
            pass
        feat_vec = FeatureBuilder.extract_features(
            integrity_data={"matches": (integrity_status == "VERIFIED")},
            vuln_data={"critical_count": critical_c, "high_count": high_c, "medium_count": med_c, "low_count": low_c, "total_findings": critical_c + high_c + med_c + low_c},
            provenance_data={"mandatory_passed": prov_mandatory_passed is True},
            test_data=test_data,
            completeness_pct=completeness_pct,
            previous_vuln_count=prev_vuln_count,
            changed_evidence_items=len(evidence_list)
        )
        ai_res = self.ml_inference.predict_anomaly(feat_vec)

        # ---------------- Policy Engine Evaluation ----------------
        policy_res = PolicyEngine.evaluate_policy(
            policy=policy,
            integrity_status="MISMATCH" if integrity_status == "FAILED" else ("VERIFIED" if integrity_status == "VERIFIED" else None),
            critical_vuln_count=critical_c,
            high_vuln_count=high_c,
            provenance_mandatory_passed=prov_mandatory_passed,
            tests_mandatory_passed=test_mandatory_passed,
            evidence_complete=evidence_is_complete,
            trust_score=computed_trust_score,
            ai_anomaly_flagged=ai_res.anomaly_detected
        )

        # ---------------- Risk Factors & Recommendations ----------------
        risk_factors: List[str] = []
        if critical_c > 0 or high_c > 0:
            risk_factors.append(f"High vulnerability surface: {critical_c} critical, {high_c} high findings.")
        if integrity_status == "FAILED":
            risk_factors.append("Critical cryptographic integrity mismatch detected.")
        if prov_mandatory_passed is False:
            risk_factors.append("Build provenance failed verification.")
        if test_mandatory_passed is False:
            risk_factors.append("Security regression tests failed.")
        if not evidence_is_complete:
            risk_factors.append(f"Incomplete release evidence ({completeness_pct}% completeness).")
        if ai_res.anomaly_detected:
            risk_factors.append(f"AI anomaly detected (score: {ai_res.anomaly_score}): {ai_res.feature_importance_summary}.")

        new_version = (previous_assessment.assessment_version + 1) if previous_assessment else 1
        assessment_id = f"asm-{uuid.uuid4().hex[:10]}"

        record = AssessmentRecord(
            assessment_id=assessment_id,
            project_id=release.project_id,
            release_id=release.release_id,
            assessment_version=new_version,
            trust_score=computed_trust_score,
            decision=policy_res["decision"],
            policy_version=policy.policy_version,
            score_breakdown=breakdown,
            blocking_reasons=policy_res["blocking_reasons"],
            risk_factors=risk_factors,
            recommendations=policy_res["recommendations"],
            explanations=policy_res["explanations"],
            ai_anomaly=ai_res,
            evidence_ids_used=[ev.evidence_id for ev in latest_evidence.values()],
            previous_assessment_id=previous_assessment.assessment_id if previous_assessment else None,
            created_at=now,
            engine_version="ECTE-v1.0"
        )

        # ---------------- Evidence-Change Delta & Audit Event ----------------
        audit_event = None
        if previous_assessment is None:
            # First assessment
            audit_event = AuditEvent(
                event_id=f"evt-{uuid.uuid4().hex[:8]}",
                event_type="ASSESSMENT_CHANGED",
                project_id=release.project_id,
                release_id=release.release_id,
                previous_assessment_version=None,
                new_assessment_version=1,
                previous_decision=None,
                new_decision=record.decision,
                reason_codes=["INITIAL_RELEASE_ASSESSMENT"],
                timestamp=now,
                actor="ECTE_Engine",
                details={
                    "trust_score": record.trust_score,
                    "evidence_count": len(evidence_list)
                }
            )
        else:
            # Check for changes in decision, score, or evidence
            decision_changed = previous_assessment.decision != record.decision
            score_changed = previous_assessment.trust_score != record.trust_score
            reasons = []

            if integrity_status == "FAILED" and (previous_assessment.score_breakdown.integrity_score or 100) > 0:
                reasons.append("ARTIFACT_HASH_MISMATCH")
            if critical_c > 0:
                reasons.append("CRITICAL_VULNERABILITY_DETECTED")
            if prov_mandatory_passed is False:
                reasons.append("PROVENANCE_FAILED")
            if test_mandatory_passed is False:
                reasons.append("TESTS_FAILED")
            if ai_res.anomaly_detected and not (previous_assessment.ai_anomaly and previous_assessment.ai_anomaly.anomaly_detected):
                reasons.append("AI_ANOMALY_TRIGGERED")
            if decision_changed:
                reasons.append(f"DECISION_{previous_assessment.decision}_TO_{record.decision}")

            if not reasons:
                reasons.append("EVIDENCE_UPDATED")

            audit_event = AuditEvent(
                event_id=f"evt-{uuid.uuid4().hex[:8]}",
                event_type="ASSESSMENT_CHANGED",
                project_id=release.project_id,
                release_id=release.release_id,
                previous_assessment_version=previous_assessment.assessment_version,
                new_assessment_version=record.assessment_version,
                previous_decision=previous_assessment.decision,
                new_decision=record.decision,
                reason_codes=reasons,
                timestamp=now,
                actor="ECTE_Engine",
                details={
                    "previous_score": previous_assessment.trust_score,
                    "new_score": record.trust_score,
                    "blocking_reasons": record.blocking_reasons
                }
            )

        return record, audit_event
