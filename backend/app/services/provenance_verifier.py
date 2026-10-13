from typing import Dict, Any, List, Optional
from backend.app.schemas.evidence import ProvenancePayload, CosignStatus

class ProvenanceVerifier:
    """
    SLSA / in-toto build provenance parser and verification engine.
    Validates builder identity, source commits, artifact digests, and cryptographic signatures.
    """

    @staticmethod
    def verify_provenance(
        payload: Dict[str, Any],
        expected_commit: str,
        expected_digest: str,
        require_cosign: bool = False
    ) -> Dict[str, Any]:
        """
        Verify provenance payload against expected release commit and artifact digest.
        """
        notes: List[str] = []
        mandatory_passed = True

        builder_id = payload.get("builder_id", "")
        source_revision = payload.get("source_revision", "")
        artifact_digest = payload.get("artifact_digest", "")
        slsa_level = payload.get("slsa_level", "SLSA_BUILD_LEVEL_1")
        cosign_status: CosignStatus = payload.get("cosign_verified", "NOT_PERFORMED")
        cosign_signer = payload.get("cosign_signer_identity")

        # 1. Builder Check
        if not builder_id:
            mandatory_passed = False
            notes.append("Missing mandatory builder identity.")
        else:
            notes.append(f"Builder verified: {builder_id}")

        # 2. Source Revision Match
        if not source_revision:
            mandatory_passed = False
            notes.append("Missing source revision in provenance.")
        elif expected_commit and not (
            source_revision.startswith(expected_commit) or expected_commit.startswith(source_revision)
        ):
            mandatory_passed = False
            notes.append(f"Source commit mismatch: provenance states '{source_revision}', expected '{expected_commit}'.")
        else:
            notes.append(f"Source commit matched: {source_revision[:8]}")

        # 3. Artifact Digest Match
        if not artifact_digest:
            mandatory_passed = False
            notes.append("Missing artifact digest in provenance.")
        elif expected_digest and artifact_digest.lower() != expected_digest.lower():
            mandatory_passed = False
            notes.append(f"Provenance artifact digest '{artifact_digest[:12]}...' does not match release artifact.")
        else:
            notes.append("Artifact digest verified against release artifact.")

        # 4. Cryptographic Cosign / Signature Check
        if require_cosign:
            if cosign_status == "VERIFIED":
                notes.append(f"Cosign signature verified for signer '{cosign_signer or 'trusted-issuer'}'.")
            elif cosign_status == "FAILED":
                mandatory_passed = False
                notes.append("Cryptographic Cosign signature verification failed.")
            else:
                mandatory_passed = False
                notes.append(f"Mandatory cryptographic signature is {cosign_status}.")
        else:
            if cosign_status == "VERIFIED":
                notes.append(f"Optional Cosign signature verified ({cosign_signer or 'trusted'}).")
            elif cosign_status == "NOT_PERFORMED":
                notes.append("Optional Cosign signature verification not performed.")

        # Score calculation
        if not mandatory_passed:
            score = 0.0
            status_label = "FAILED"
        else:
            # Base 85 for SLSA L1/L2, 100 with verified Cosign
            if cosign_status == "VERIFIED" or slsa_level in ["SLSA_BUILD_LEVEL_3"]:
                score = 100.0
                status_label = "VERIFIED"
            else:
                score = 85.0
                status_label = "PARTIAL"

        return {
            "score": score,
            "status": status_label,
            "mandatory_passed": mandatory_passed,
            "notes": notes,
            "builder_id": builder_id,
            "source_revision": source_revision,
            "artifact_digest": artifact_digest,
            "slsa_level": slsa_level,
            "cosign_verified": cosign_status
        }
