import hashlib
import json
from typing import BinaryIO, Any, Dict

def calculate_sha256_stream(file_obj: BinaryIO, chunk_size: int = 65536) -> str:
    """Calculate streaming SHA-256 for a file-like binary stream."""
    hasher = hashlib.sha256()
    while chunk := file_obj.read(chunk_size):
        hasher.update(chunk)
    return hasher.hexdigest().lower()

def calculate_sha256_bytes(data: bytes) -> str:
    """Calculate SHA-256 hex digest for byte data."""
    return hashlib.sha256(data).hexdigest().lower()

def calculate_sha256_text(text: str) -> str:
    """Calculate SHA-256 hex digest for text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest().lower()

def calculate_evidence_payload_hash(payload: Dict[str, Any]) -> str:
    """
    Produce a deterministic SHA-256 hash of a JSON payload dictionary.
    Keys are sorted and JSON formatted without non-deterministic whitespace.
    """
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest().lower()
