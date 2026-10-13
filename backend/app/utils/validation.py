import re
import os
import unicodedata
from fastapi import HTTPException, status

SAFE_FILENAME_RE = re.compile(r"^[\w\-. ]+$")

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and illegal characters.
    Extracts the basename and strips dangerous characters.
    """
    clean_name = os.path.basename(filename)
    clean_name = unicodedata.normalize("NFKD", clean_name).encode("ASCII", "ignore").decode("utf-8")
    clean_name = re.sub(r"[^\w\-. ]", "_", clean_name).strip()
    if not clean_name or clean_name in (".", ".."):
        clean_name = "unnamed_artifact.bin"
    return clean_name

def validate_safe_path(base_dir: str, target_path: str) -> str:
    """
    Ensure target_path does not escape base_dir (directory traversal defense).
    """
    resolved_base = os.path.abspath(base_dir)
    resolved_target = os.path.abspath(target_path)
    if not resolved_target.startswith(resolved_base):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal path traversal detected."
        )
    return resolved_target

def generate_s3_artifact_key(project_id: str, version: str, filename: str) -> str:
    """Generate safe, structured S3 object key."""
    clean_proj = re.sub(r"[^\w\-]", "_", project_id)
    clean_ver = re.sub(r"[^\w\-.]", "_", version)
    clean_file = sanitize_filename(filename)
    return f"artifacts/{clean_proj}/{clean_ver}/{clean_file}"
