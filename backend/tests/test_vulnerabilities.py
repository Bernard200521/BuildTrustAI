from backend.app.schemas.evidence import VulnFinding
from backend.app.services.vulnerability_service import VulnerabilityService

def test_vulnerability_scoring_formula():
    # D = max(0, 100 - 40C - 20H - 8M - 2L)
    findings = [
        VulnFinding(id="CVE-1", package="pkg1", version="1.0", severity="CRITICAL"),
        VulnFinding(id="CVE-2", package="pkg2", version="1.0", severity="HIGH"),
        VulnFinding(id="CVE-3", package="pkg3", version="1.0", severity="MEDIUM"),
        VulnFinding(id="CVE-4", package="pkg4", version="1.0", severity="LOW"),
    ]
    # Expected penalty: 40 + 20 + 8 + 2 = 70. Score = 30.0
    res = VulnerabilityService.calculate_dependency_score(findings)
    assert res["score"] == 30.0
    assert res["critical_count"] == 1
    assert res["high_count"] == 1
    assert res["medium_count"] == 1
    assert res["low_count"] == 1

def test_vulnerability_deduplication():
    # Duplicate findings for the same package and CVE should be counted once
    findings = [
        VulnFinding(id="CVE-1", package="libA", version="1.0", severity="CRITICAL"),
        VulnFinding(id="CVE-1", package="libA", version="1.0", severity="CRITICAL")
    ]
    res = VulnerabilityService.calculate_dependency_score(findings)
    assert res["critical_count"] == 1
    assert res["score"] == 60.0 # 100 - 40*1
