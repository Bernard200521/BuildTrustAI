import io
import hashlib
from backend.app.services.artifact_verifier import ArtifactVerifier

def test_artifact_matching_hash():
    content = b"Binary release build content for test service"
    expected_sha = hashlib.sha256(content).hexdigest()
    
    stream = io.BytesIO(content)
    result = ArtifactVerifier.verify_file_stream(stream, expected_sha, "test_build.zip")
    
    assert result["matches"] is True
    assert result["status"] == "VERIFIED"
    assert result["calculated_sha256"] == expected_sha
    assert result["byte_size"] == len(content)

def test_artifact_tampered_hash_mismatch():
    content = b"Original build payload"
    tampered_content = b"Tampered build payload injected with backdoor"
    expected_sha = hashlib.sha256(content).hexdigest()
    
    stream = io.BytesIO(tampered_content)
    result = ArtifactVerifier.verify_file_stream(stream, expected_sha, "tampered_build.zip")
    
    assert result["matches"] is False
    assert result["status"] == "MISMATCH"
    assert result["calculated_sha256"] != expected_sha
