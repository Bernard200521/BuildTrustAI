from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.assessment import AssessmentRecord
from backend.app.schemas.audit import AuditEvent
from backend.app.services.trust_engine import TrustEngine
from backend.app.services.event_service import broadcaster

class AssessmentService:
    def __init__(self, repo: BaseRepository, trust_engine: Optional[TrustEngine] = None):
        self.repo = repo
        self.trust_engine = trust_engine or TrustEngine()

    async def trigger_reassessment(self, release_id: str, actor: str = "system") -> AssessmentRecord:
        """
        Orchestrate release reassessment with ECTE engine, persist results,
        record audit trail, and publish live event to dashboard.
        """
        release = self.repo.get_release(release_id)
        if not release:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Release '{release_id}' not found."
            )

        project = self.repo.get_project(release.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{release.project_id}' not found."
            )

        evidence_list = self.repo.list_evidence_for_release(release_id)
        previous_assessment = self.repo.get_latest_assessment(release_id)

        # Execute ECTE assessment
        assessment, audit_event = self.trust_engine.assess_release(
            release=release,
            policy=project.policy,
            evidence_list=evidence_list,
            previous_assessment=previous_assessment
        )

        # 1. Persist Assessment
        self.repo.save_assessment(assessment)

        # 2. Update Release Metadata
        self.repo.update_release_status(
            release_id=release_id,
            decision=assessment.decision,
            trust_score=assessment.trust_score,
            assessment_id=assessment.assessment_id
        )

        # 3. Persist and Broadcast Audit Event
        if audit_event:
            audit_event.actor = actor
            self.repo.record_audit_event(audit_event)

            # Determine specific outcome event type
            evt_type = "ASSESSMENT_CHANGED"
            if assessment.decision == "BLOCK":
                evt_type = "POLICY_BLOCKED"
            elif assessment.decision == "APPROVE":
                evt_type = "RELEASE_APPROVED"
            elif assessment.decision == "INSUFFICIENT_EVIDENCE":
                evt_type = "INSUFFICIENT_EVIDENCE"

            is_demo = "demo" in actor.lower() or "scenario" in actor.lower()
            now = audit_event.timestamp
            summary = (
                f"Release {release_id} evaluated with ECTE: Decision {assessment.decision}, "
                f"Trust Score {assessment.trust_score} (Assessment v{assessment.assessment_version})."
            )
            if assessment.blocking_reasons:
                summary += f" Blocking: {'; '.join(assessment.blocking_reasons)}"

            # Broadcast to live dashboard via SSE
            await broadcaster.broadcast({
                "event_id": audit_event.event_id,
                "event_type": evt_type,
                "type": evt_type,
                "occurred_at": now,
                "timestamp": now,
                "project_id": release.project_id,
                "release_id": release_id,
                "correlation_id": f"corr-asm-{assessment.assessment_id}",
                "actor": actor,
                "decision": assessment.decision,
                "trust_score": assessment.trust_score,
                "assessment_version": assessment.assessment_version,
                "reason_codes": audit_event.reason_codes or [f"DECISION_{assessment.decision}"],
                "summary": summary,
                "is_demo": is_demo,
                "details": {
                    "assessment_id": assessment.assessment_id,
                    "blocking_reasons": assessment.blocking_reasons,
                    "risk_factors": assessment.risk_factors
                }
            })

        return assessment

    def get_latest_assessment(self, release_id: str) -> Optional[AssessmentRecord]:
        return self.repo.get_latest_assessment(release_id)

    def list_history(self, release_id: str) -> List[AssessmentRecord]:
        return self.repo.list_assessments(release_id)
