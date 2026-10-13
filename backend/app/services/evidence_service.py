import uuid
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.evidence import (
    EvidenceEnvelope,
    EvidenceSubmission,
    EvidenceType,
    ArtifactIntegrityPayload,
    SBOMPayload,
    VulnerabilityScanPayload,
    ProvenancePayload,
    TestResultsPayload
)
from backend.app.schemas.audit import AuditEvent
from backend.app.utils.hashing import calculate_evidence_payload_hash
from backend.app.utils.timestamps import utc_now_iso

class EvidenceService:
    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def ingest_evidence(
        self,
        release_id: str,
        submission: EvidenceSubmission,
        actor: str = "cli_agent"
    ) -> Tuple[EvidenceEnvelope, bool]:
        """
        Ingest, validate, and deduplicate release evidence.
        Returns (EvidenceEnvelope, is_duplicate).
        """
        release = self.repo.get_release(release_id)
        if not release:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Release '{release_id}' not found."
            )

        # 1. Validate payload schema according to evidence_type
        self._validate_payload_schema(submission.evidence_type, submission.payload)

        # 2. Compute canonical deterministic payload hash
        content_sha256 = calculate_evidence_payload_hash(submission.payload)

        # 3. Deduplication check
        if self.repo.is_evidence_duplicate(release_id, submission.evidence_type, content_sha256):
            # Fetch existing evidence
            all_ev = self.repo.list_evidence_for_release(release_id)
            for ev in all_ev:
                if ev.evidence_type == submission.evidence_type and ev.content_sha256 == content_sha256:
                    return ev, True

        now = utc_now_iso()
        ev_id = submission.evidence_id or f"ev-{uuid.uuid4().hex[:10]}"
        corr_id = submission.correlation_id or f"corr-{release_id}-{uuid.uuid4().hex[:6]}"

        # Determine version for this evidence type
        existing = [e for e in self.repo.list_evidence_for_release(release_id) if e.evidence_type == submission.evidence_type]
        next_ver = len(existing) + 1

        envelope = EvidenceEnvelope(
            evidence_id=ev_id,
            project_id=release.project_id,
            release_id=release_id,
            evidence_type=submission.evidence_type,
            schema_version="1.0",
            evidence_version=next_ver,
            source=submission.source,
            observed_at=submission.observed_at or now,
            received_at=now,
            validation_status="valid",
            payload=submission.payload,
            content_sha256=content_sha256,
            correlation_id=corr_id
        )

        saved = self.repo.save_evidence(envelope)

        # Record audit event
        audit_event = AuditEvent(
            event_id=f"evt-{uuid.uuid4().hex[:8]}",
            event_type="EVIDENCE_SUBMITTED",
            project_id=release.project_id,
            release_id=release_id,
            timestamp=now,
            actor=actor,
            reason_codes=[f"EVIDENCE_TYPE_{submission.evidence_type.upper()}"],
            details={
                "evidence_id": ev_id,
                "evidence_type": submission.evidence_type,
                "evidence_version": next_ver,
                "content_sha256": content_sha256
            }
        )
        self.repo.record_audit_event(audit_event)

        return saved, False

    def list_evidence(self, release_id: str) -> List[EvidenceEnvelope]:
        return self.repo.list_evidence_for_release(release_id)

    def _validate_payload_schema(self, ev_type: EvidenceType, payload: Dict[str, Any]):
        """Strict Pydantic schema validation for evidence payloads."""
        try:
            if ev_type == "artifact_integrity":
                ArtifactIntegrityPayload(**payload)
            elif ev_type == "sbom":
                SBOMPayload(**payload)
            elif ev_type == "vulnerability_scan":
                VulnerabilityScanPayload(**payload)
            elif ev_type == "provenance":
                ProvenancePayload(**payload)
            elif ev_type == "test_results":
                TestResultsPayload(**payload)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid payload for evidence type '{ev_type}': {str(e)}"
            )
