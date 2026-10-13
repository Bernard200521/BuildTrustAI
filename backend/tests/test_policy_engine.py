from backend.app.schemas.project import ProjectPolicy
from backend.app.services.policy_engine import PolicyEngine

def test_mandatory_hash_mismatch_blocks_release():
    policy = ProjectPolicy(approval_threshold=85.0)
    res = PolicyEngine.evaluate_policy(
        policy=policy,
        integrity_status="MISMATCH",
        critical_vuln_count=0,
        high_vuln_count=0,
        provenance_mandatory_passed=True,
        tests_mandatory_passed=True,
        evidence_complete=True,
        trust_score=95.0, # High score must still be blocked!
        ai_anomaly_flagged=False
    )
    assert res["decision"] == "BLOCK"
    assert any("cryptographic SHA-256" in r for r in res["blocking_reasons"])

def test_critical_vulnerability_blocks_release():
    policy = ProjectPolicy(block_on_critical_vuln=True)
    res = PolicyEngine.evaluate_policy(
        policy=policy,
        integrity_status="VERIFIED",
        critical_vuln_count=1,
        high_vuln_count=0,
        provenance_mandatory_passed=True,
        tests_mandatory_passed=True,
        evidence_complete=True,
        trust_score=88.0,
        ai_anomaly_flagged=False
    )
    assert res["decision"] == "BLOCK"
    assert any("CRITICAL" in r for r in res["blocking_reasons"])

def test_clean_release_approved():
    policy = ProjectPolicy(approval_threshold=85.0)
    res = PolicyEngine.evaluate_policy(
        policy=policy,
        integrity_status="VERIFIED",
        critical_vuln_count=0,
        high_vuln_count=0,
        provenance_mandatory_passed=True,
        tests_mandatory_passed=True,
        evidence_complete=True,
        trust_score=92.0,
        ai_anomaly_flagged=False
    )
    assert res["decision"] == "APPROVE"

def test_ai_anomaly_forces_review_not_override():
    policy = ProjectPolicy(approval_threshold=85.0)
    # High score that would normally be approved is downgraded to REVIEW due to AI anomaly
    res = PolicyEngine.evaluate_policy(
        policy=policy,
        integrity_status="VERIFIED",
        critical_vuln_count=0,
        high_vuln_count=0,
        provenance_mandatory_passed=True,
        tests_mandatory_passed=True,
        evidence_complete=True,
        trust_score=90.0,
        ai_anomaly_flagged=True
    )
    assert res["decision"] == "REVIEW"
