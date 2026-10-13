from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from backend.app.dependencies import get_repository
from backend.app.repositories.base import BaseRepository
from backend.app.services.event_service import broadcaster

router = APIRouter(prefix="/events", tags=["Live Events"])

@router.get("", response_class=EventSourceResponse)
async def subscribe_to_live_events(repo: BaseRepository = Depends(get_repository)):
    """
    Server-Sent Events (SSE) endpoint providing live, push updates to connected dashboards
    whenever evidence is ingested or an assessment decision changes.
    """
    initial_events = None
    if not broadcaster._history:
        recent_audits = repo.list_audit_events(limit=20)
        initial_events = []
        for a in reversed(recent_audits):
            initial_events.append({
                "event_id": a.event_id,
                "event_type": a.event_type,
                "type": a.event_type,
                "occurred_at": a.timestamp,
                "timestamp": a.timestamp,
                "release_id": a.release_id,
                "project_id": a.project_id,
                "actor": a.actor,
                "reason_codes": a.reason_codes,
                "summary": f"{a.event_type} on {a.release_id} recorded by {a.actor}.",
                "decision": a.new_decision,
                "is_demo": "demo" in a.actor.lower(),
                "details": a.details
            })

    return EventSourceResponse(
        broadcaster.subscribe(initial_events=initial_events),
        ping=15,
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
