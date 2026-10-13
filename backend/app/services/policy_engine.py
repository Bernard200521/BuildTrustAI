from typing import List, Dict, Any, Optional
from backend.app.schemas.project import ProjectPolicy
from backend.app.schemas.assessment import DecisionType, ExplanationItem

class PolicyEngine:
    """
    Deterministic security policy evaluation engine.
    Mandatory blocking conditions always take precedence over AI scoring signals.
    """

    @staticmethod
    def evaluate_policy(
        policy: ProjectPolicy,
        integrity_status: Optional[str],
        critical_vuln_count: int,
        high_vuln_count: int,
        provenance_mandatory_passed: Optional[bool],
        tests_mandatory_passed: Optional[bool],
        evidence_complete: bool,
        trust_score: Optional[float],
        ai_anomaly_flagged: bool = False,
        unauthorized: bool = False
    ) -> Dict[str, Any]:
        blocking_reasons: List[str] = []
        recommendations: List[str] = []
        explanations: List[ExplanationItem] = []

        # 1. Mandatory Security Rule: Unauthorized submission
        if unauthorized:
            blocking_reasons.append("Unauthorized release modification detected.")
            recommendations.append("Ensure submitter possesses proper DEVELOPER role authorization.")
            explanations.append(ExplanationItem(
                rule_or_factor="AUTHORIZATION_POLICY",
                impact="BLOCK",
                message="Caller lacks authorization for this project or release."
            ))
            return {
                "decision": "BLOCK",
                "blocking_reasons": blocking_reasons,
                "recommendations": recommendations,
                "explanations": explanations
            }

        # 2. Mandatory Security Rule: Artifact Integrity
        if integrity_status == "MISMATCH":
            blocking_reasons.append("Artifact cryptographic SHA-256 digest does not match trusted reference (possible tampering or corrupted artifact).")
            recommendations.append("Investigate artifact build pipeline or re-verify expected cryptographic digest.")
            explanations.append(ExplanationItem(
                rule_or_factor="MANDATORY_INTEGRITY_POLICY",
                impact="BLOCK",
                message="Artifact SHA-256 mismatch detected. Immediate block triggered."
            ))

        # 3. Mandatory Security Rule: Critical Vulnerability
        if policy.block_on_critical_vuln and critical_vuln_count > 0:
            blocking_reasons.append(f"Release contains {critical_vuln_count} verified CRITICAL vulnerability finding(s).")
            recommendations.append(f"Upgrade affected packages or apply security patches to eliminate critical vulnerabilities.")
            explanations.append(ExplanationItem(
                rule_or_factor="VULNERABILITY_THRESHOLD_POLICY",
                impact="BLOCK",
                message=f"Zero-tolerance policy for critical CVEs triggered ({critical_vuln_count} critical findings)."
            ))

        # 4. Mandatory Security Rule: High Vulnerability Count
        if high_vuln_count >= policy.block_on_high_vuln_count:
            blocking_reasons.append(f"Release contains {high_vuln_count} HIGH severity vulnerabilities (limit: {policy.block_on_high_vuln_count}).")
            recommendations.append("Remediate high-severity dependency vulnerabilities before promotion.")
            explanations.append(ExplanationItem(
                rule_or_factor="HIGH_VULNERABILITY_LIMIT_POLICY",
                impact="BLOCK",
                message=f"Exceeded high-severity vulnerability tolerance threshold."
            ))

        # 5. Mandatory Security Rule: Provenance Failure
        if policy.require_provenance and provenance_mandatory_passed is False:
            blocking_reasons.append("Mandatory build provenance verification failed (builder or commit mismatch).")
            recommendations.append("Ensure build is produced by authorized CI/CD builder and matches release commit tag.")
            explanations.append(ExplanationItem(
                rule_or_factor="PROVENANCE_POLICY",
                impact="BLOCK",
                message="Build provenance failed validation criteria."
            ))

        # 6. Mandatory Security Rule: Mandatory Tests Failure
        if policy.require_tests and tests_mandatory_passed is False:
            blocking_reasons.append("Mandatory security regression or unit test suite failed.")
            recommendations.append("Fix failing test suites in CI pipeline.")
            explanations.append(ExplanationItem(
                rule_or_factor="TEST_SUITE_POLICY",
                impact="BLOCK",
                message="Mandatory security tests failed."
            ))

        # If any mandatory condition was breached, return immediate BLOCK
        if blocking_reasons:
            return {
                "decision": "BLOCK",
                "blocking_reasons": blocking_reasons,
                "recommendations": recommendations,
                "explanations": explanations
            }

        # 7. Evidence Completeness Check
        if not evidence_complete:
            recommendations.append("Submit all required release evidence envelopes (SBOM, Provenance, Tests, Vulnerability Scan, Artifact).")
            explanations.append(ExplanationItem(
                rule_or_factor="EVIDENCE_COMPLETENESS_POLICY",
                impact="PENALTY",
                message="Release evidence is incomplete; required items are missing or unverified."
            ))
            return {
                "decision": "INSUFFICIENT_EVIDENCE",
                "blocking_reasons": ["Incomplete required evidence."],
                "recommendations": recommendations,
                "explanations": explanations
            }

        # 8. AI Anomaly Prioritization Check
        if ai_anomaly_flagged:
            recommendations.append("Release flagged by AI anomaly detection due to unusual multidimensional risk profile. Requires manual SecOps review.")
            explanations.append(ExplanationItem(
                rule_or_factor="AI_ANOMALY_MONITOR",
                impact="PENALTY",
                message="IsolationForest detected anomalous release feature combination."
            ))
            # AI Anomaly downgrades APPROVE to REVIEW, never forces APPROVE
            if trust_score is not None and trust_score >= policy.approval_threshold:
                return {
                    "decision": "REVIEW",
                    "blocking_reasons": [],
                    "recommendations": recommendations,
                    "explanations": explanations
                }

        # 9. Trust Score Threshold Gates
        if trust_score is None:
            return {
                "decision": "REVIEW",
                "blocking_reasons": ["Trust score could not be calculated."],
                "recommendations": recommendations,
                "explanations": explanations
            }

        if trust_score >= policy.approval_threshold:
            explanations.append(ExplanationItem(
                rule_or_factor="TRUST_THRESHOLD_APPROVAL",
                impact="POSITIVE",
                message=f"Release trust score ({trust_score}) satisfies approval threshold (>= {policy.approval_threshold})."
            ))
            return {
                "decision": "APPROVE",
                "blocking_reasons": [],
                "recommendations": ["Release candidate meets all security policies and is cleared for deployment."],
                "explanations": explanations
            }
        elif trust_score >= policy.review_threshold:
            explanations.append(ExplanationItem(
                rule_or_factor="TRUST_THRESHOLD_REVIEW",
                impact="PENALTY",
                message=f"Trust score ({trust_score}) is below approval threshold ({policy.approval_threshold}) but above block threshold ({policy.review_threshold})."
            ))
            recommendations.append("Address moderate dependency vulnerabilities or test warnings to improve trust score to approval threshold.")
            return {
                "decision": "REVIEW",
                "blocking_reasons": [],
                "recommendations": recommendations,
                "explanations": explanations
            }
        else:
            explanations.append(ExplanationItem(
                rule_or_factor="TRUST_THRESHOLD_BLOCK",
                impact="BLOCK",
                message=f"Trust score ({trust_score}) is below minimum acceptable release score (< {policy.review_threshold})."
            ))
            blocking_reasons.append(f"Trust score {trust_score} below minimum threshold {policy.review_threshold}.")
            recommendations.append("Remediate identified risk factors to raise trust score.")
            return {
                "decision": "BLOCK",
                "blocking_reasons": blocking_reasons,
                "recommendations": recommendations,
                "explanations": explanations
            }
