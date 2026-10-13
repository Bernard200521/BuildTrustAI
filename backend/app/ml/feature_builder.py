from typing import Dict, Any, List, Optional
import numpy as np

FEATURE_NAMES = [
    "norm_vuln_crit",
    "norm_vuln_high",
    "norm_vuln_med",
    "max_vuln_severity_code",
    "integrity_status_code",
    "provenance_status_code",
    "evidence_completeness_pct",
    "test_pass_rate_pct",
    "test_mandatory_passed",
    "delta_vuln_count",
    "evidence_changed_count"
]

class FeatureBuilder:
    """
    Constructs normalized numerical feature vectors from verified release evidence
    for AI/ML anomaly detection and risk prioritization.
    """

    @staticmethod
    def extract_features(
        integrity_data: Optional[Dict[str, Any]],
        vuln_data: Optional[Dict[str, Any]],
        provenance_data: Optional[Dict[str, Any]],
        test_data: Optional[Dict[str, Any]],
        completeness_pct: float,
        previous_vuln_count: int = 0,
        changed_evidence_items: int = 0
    ) -> List[float]:
        # 1. Vulnerabilities
        c_count = 0
        h_count = 0
        m_count = 0
        max_sev = 0
        total_vulns = 0

        if vuln_data:
            c_count = vuln_data.get("critical_count", 0)
            h_count = vuln_data.get("high_count", 0)
            m_count = vuln_data.get("medium_count", 0)
            total_vulns = vuln_data.get("total_findings", 0)
            if c_count > 0:
                max_sev = 4
            elif h_count > 0:
                max_sev = 3
            elif m_count > 0:
                max_sev = 2
            elif vuln_data.get("low_count", 0) > 0:
                max_sev = 1

        norm_c = min(5.0, float(c_count)) / 5.0
        norm_h = min(10.0, float(h_count)) / 10.0
        norm_m = min(20.0, float(m_count)) / 20.0

        # 2. Integrity
        int_code = 1.0 if (integrity_data and integrity_data.get("matches", False)) else 0.0

        # 3. Provenance
        prov_code = 1.0 if (provenance_data and provenance_data.get("mandatory_passed", False)) else 0.0

        # 4. Tests
        test_pass_rate = 0.0
        test_mandatory = 0.0
        if test_data:
            total_t = test_data.get("total_tests", 0)
            passed_t = test_data.get("passed", 0)
            test_pass_rate = (passed_t / total_t * 100.0) if total_t > 0 else 0.0
            test_mandatory = 1.0 if test_data.get("mandatory_passed", True) else 0.0

        # 5. Deltas
        delta_vulns = float(total_vulns - previous_vuln_count)
        changed_items = float(changed_evidence_items)

        return [
            round(norm_c, 4),
            round(norm_h, 4),
            round(norm_m, 4),
            float(max_sev),
            float(int_code),
            float(prov_code),
            round(completeness_pct, 2),
            round(test_pass_rate, 2),
            float(test_mandatory),
            float(delta_vulns),
            float(changed_items)
        ]
