import io
import time
from typing import Optional, Dict, Any, BinaryIO
from backend.app.utils.hashing import calculate_sha256_stream, calculate_sha256_bytes

class ArtifactVerifier:
    """
    Verifies software release artifacts against trusted cryptographic digests.
    Computes streaming SHA-256 digests on actual files to avoid memory exhaustion.
    """

    @staticmethod
    def verify_file_stream(file_obj: BinaryIO, expected_sha256: str, filename: str) -> Dict[str, Any]:
        """Compute real SHA-256 for a file stream and compare with expected hash."""
        start_time = time.perf_counter()
        pos = file_obj.tell() if hasattr(file_obj, "tell") else 0
        file_obj.seek(0)
        
        calculated_sha = calculate_sha256_stream(file_obj)
        byte_size = file_obj.tell()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        matches = calculated_sha.lower() == expected_sha256.strip().lower()

        return {
            "filename": filename,
            "calculated_sha256": calculated_sha,
            "expected_sha256": expected_sha256.strip().lower(),
            "matches": matches,
            "byte_size": byte_size,
            "verification_time_ms": round(elapsed_ms, 2),
            "status": "VERIFIED" if matches else "MISMATCH"
        }

    @staticmethod
    def verify_bytes(data: bytes, expected_sha256: str, filename: str) -> Dict[str, Any]:
        """Verify byte buffer against expected SHA-256."""
        start_time = time.perf_counter()
        calculated_sha = calculate_sha256_bytes(data)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        matches = calculated_sha.lower() == expected_sha256.strip().lower()

        return {
            "filename": filename,
            "calculated_sha256": calculated_sha,
            "expected_sha256": expected_sha256.strip().lower(),
            "matches": matches,
            "byte_size": len(data),
            "verification_time_ms": round(elapsed_ms, 2),
            "status": "VERIFIED" if matches else "MISMATCH"
        }
