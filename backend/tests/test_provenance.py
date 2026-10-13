from backend.app.services.provenance_verifier import ProvenanceVerifier

def test_provenance_valid_verification():
    payload = {
        "builder_id": "https://github.com/BuildTrustAI/actions/runner@v3",
        "source_revision": "abc12345",
        "artifact_digest": "abcdef64charsabcdef64charsabcdef64charsabcdef64charsabcdef64char",
        "slsa_level": "SLSA_BUILD_LEVEL_2",
        "cosign_verified": "VERIFIED"
    }
    res = ProvenanceVerifier.verify_provenance(
        payload=payload,
        expected_commit="abc12345",
        expected_digest="abcdef64charsabcdef64charsabcdef64charsabcdef64charsabcdef64char"
    )
    assert res["mandatory_passed"] is True
    assert res["status"] == "VERIFIED"
    assert res["score"] == 100.0

def test_provenance_commit_mismatch_failure():
    payload = {
        "builder_id": "https://trusted-builder.org",
        "source_revision": "unauthorized-branch-commit",
        "artifact_digest": "matching-digest",
        "slsa_level": "SLSA_BUILD_LEVEL_1"
    }
    res = ProvenanceVerifier.verify_provenance(
        payload=payload,
        expected_commit="expected-release-commit",
        expected_digest="matching-digest"
    )
    assert res["mandatory_passed"] is False
    assert res["status"] == "FAILED"
    assert res["score"] == 0.0
