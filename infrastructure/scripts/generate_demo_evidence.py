import os
import zipfile
import json
import hashlib

def create_sample_files():
    base = "sample_data"
    os.makedirs(f"{base}/manifests", exist_ok=True)
    os.makedirs(f"{base}/sbom", exist_ok=True)
    os.makedirs(f"{base}/provenance", exist_ok=True)
    os.makedirs(f"{base}/vulnerability_reports", exist_ok=True)
    os.makedirs(f"{base}/test_results", exist_ok=True)
    os.makedirs(f"{base}/evaluation", exist_ok=True)

    # 1. Real Artifact
    artifact_path = f"{base}/payment-service-1.0.0.zip"
    with zipfile.ZipFile(artifact_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("app.py", "def handle_payment(): return {'status': 'processed'}\n")
        z.writestr("config.json", json.dumps({"environment": "staging", "version": "1.0.0"}))
    
    with open(artifact_path, "rb") as f:
        clean_sha256 = hashlib.sha256(f.read()).hexdigest().lower()
    print(f"Generated clean artifact: {artifact_path} (SHA-256: {clean_sha256})")

    # Tampered Artifact
    tampered_path = f"{base}/payment-service-tampered.zip"
    with zipfile.ZipFile(tampered_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("app.py", "def handle_payment(): return {'tampered': True}\n")
        z.writestr("config.json", json.dumps({"environment": "staging", "version": "1.0.0-tampered"}))
    with open(tampered_path, "rb") as f:
        tampered_sha256 = hashlib.sha256(f.read()).hexdigest().lower()
    print(f"Generated tampered artifact: {tampered_path} (SHA-256: {tampered_sha256})")

    # 2. Manifests
    manifest_clean = {
        "project_id": "demo-payment-service",
        "release_id": "rel-001",
        "version": "1.0.0",
        "source_commit": "a1b2c3d4e5f67890",
        "artifact": {
            "filename": "payment-service-1.0.0.zip",
            "s3_key": "artifacts/demo-payment-service/1.0.0/payment-service-1.0.0.zip",
            "expected_sha256": clean_sha256
        },
        "evidence_requirements": {
            "sbom_required": True,
            "provenance_required": True,
            "tests_required": True,
            "dependency_scan_required": True
        },
        "policy_version": "1.0",
        "environment": "staging"
    }
    with open(f"{base}/manifests/payment-service-1.0.0.json", "w") as f:
        json.dump(manifest_clean, f, indent=2)

    # 3. Clean SBOM (CycloneDX)
    sbom_clean = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
        "version": 1,
        "metadata": {
            "timestamp": "2026-10-10T12:00:00Z",
            "component": {
                "name": "payment-service",
                "version": "1.0.0",
                "type": "application"
            }
        },
        "components": [
            {
                "name": "cryptography",
                "version": "42.0.5",
                "type": "library",
                "purl": "pkg:pypi/cryptography@42.0.5",
                "licenses": [{"license": {"id": "Apache-2.0"}}]
            },
            {
                "name": "fastapi",
                "version": "0.110.0",
                "type": "library",
                "purl": "pkg:pypi/fastapi@0.110.0",
                "licenses": [{"license": {"id": "MIT"}}]
            },
            {
                "name": "requests",
                "version": "2.31.0",
                "type": "library",
                "purl": "pkg:pypi/requests@2.31.0",
                "licenses": [{"license": {"id": "Apache-2.0"}}]
            }
        ]
    }
    with open(f"{base}/sbom/cyclonedx-clean.json", "w") as f:
        json.dump(sbom_clean, f, indent=2)

    # Vulnerable SBOM
    sbom_vuln = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "components": [
            {
                "name": "log4j-core",
                "version": "2.14.1",
                "type": "library",
                "purl": "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1"
            },
            {
                "name": "urllib3",
                "version": "1.26.4",
                "type": "library",
                "purl": "pkg:pypi/urllib3@1.26.4"
            }
        ]
    }
    with open(f"{base}/sbom/cyclonedx-vulnerable.json", "w") as f:
        json.dump(sbom_vuln, f, indent=2)

    # 4. Provenance (SLSA v1.0)
    prov_valid = {
        "builder_id": "https://github.com/BuildTrustAI/actions/runner@v3",
        "build_type": "https://slsa.dev/provenance/v1",
        "source_revision": "a1b2c3d4e5f67890",
        "artifact_digest": clean_sha256,
        "slsa_level": "SLSA_BUILD_LEVEL_2",
        "invocation_entry_point": ".github/workflows/release.yml",
        "cosign_verified": "VERIFIED",
        "cosign_signer_identity": "buildtrust-signer@iam.gserviceaccount.com"
    }
    with open(f"{base}/provenance/provenance-valid.json", "w") as f:
        json.dump(prov_valid, f, indent=2)

    prov_invalid = {
        "builder_id": "https://untrusted-unauthorized-builder.org/agent",
        "build_type": "https://slsa.dev/provenance/v1",
        "source_revision": "deadbeef00000000",
        "artifact_digest": "0000000000000000000000000000000000000000000000000000000000000000",
        "slsa_level": "SLSA_BUILD_LEVEL_0",
        "cosign_verified": "FAILED",
        "cosign_signer_identity": None
    }
    with open(f"{base}/provenance/provenance-invalid.json", "w") as f:
        json.dump(prov_invalid, f, indent=2)

    # 5. Vulnerability Scans
    vuln_clean = {
        "scanner_name": "OSV-Scanner",
        "scan_timestamp": "2026-10-10T12:05:00Z",
        "total_findings": 0,
        "critical_count": 0,
        "high_count": 0,
        "medium_count": 0,
        "low_count": 0,
        "findings": [],
        "offline_fallback": False
    }
    with open(f"{base}/vulnerability_reports/vuln-clean.json", "w") as f:
        json.dump(vuln_clean, f, indent=2)

    vuln_critical = {
        "scanner_name": "OSV-Scanner",
        "scan_timestamp": "2026-10-10T12:15:00Z",
        "total_findings": 2,
        "critical_count": 1,
        "high_count": 1,
        "medium_count": 0,
        "low_count": 0,
        "findings": [
            {
                "id": "GHSA-jfh8-c2jp-5v3q",
                "package": "log4j-core",
                "version": "2.14.1",
                "severity": "CRITICAL",
                "cvss_score": 10.0,
                "summary": "Remote code execution vulnerability in Log4j (Log4Shell)",
                "advisory_url": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228",
                "fixed_version": "2.17.1",
                "source": "OSV"
            },
            {
                "id": "PYSEC-2021-108",
                "package": "urllib3",
                "version": "1.26.4",
                "severity": "HIGH",
                "cvss_score": 7.5,
                "summary": "Improper handling of stripped headers in cross-origin redirects",
                "advisory_url": "https://github.com/urllib3/urllib3/security/advisories/GHSA-q2q7-5pp4-w6pg",
                "fixed_version": "1.26.5",
                "source": "OSV"
            }
        ],
        "offline_fallback": False
    }
    with open(f"{base}/vulnerability_reports/vuln-critical.json", "w") as f:
        json.dump(vuln_critical, f, indent=2)

    # 6. Test Results
    tests_passed = {
        "test_framework": "pytest",
        "total_tests": 45,
        "passed": 45,
        "failed": 0,
        "skipped": 0,
        "mandatory_tests_passed": True,
        "coverage_percentage": 94.5,
        "suites": [
            {"name": "unit_tests", "passed": True, "duration_seconds": 3.2, "mandatory": True},
            {"name": "security_regression_suite", "passed": True, "duration_seconds": 8.5, "mandatory": True},
            {"name": "input_sanitization_checks", "passed": True, "duration_seconds": 2.1, "mandatory": True}
        ]
    }
    with open(f"{base}/test_results/tests-passed.json", "w") as f:
        json.dump(tests_passed, f, indent=2)

    tests_failed = {
        "test_framework": "pytest",
        "total_tests": 45,
        "passed": 40,
        "failed": 5,
        "skipped": 0,
        "mandatory_tests_passed": False,
        "coverage_percentage": 78.0,
        "suites": [
            {"name": "unit_tests", "passed": True, "duration_seconds": 3.1, "mandatory": True},
            {"name": "security_regression_suite", "passed": False, "duration_seconds": 5.4, "mandatory": True}
        ]
    }
    with open(f"{base}/test_results/tests-failed.json", "w") as f:
        json.dump(tests_failed, f, indent=2)

    print("All sample data fixtures generated successfully.")

if __name__ == "__main__":
    create_sample_files()
