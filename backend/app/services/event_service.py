import asyncio
import json
import logging
import uuid
from collections import deque
from typing import AsyncGenerator, Set, Dict, Any, List, Optional
from sse_starlette.sse import ServerSentEvent
from backend.app.utils.timestamps import utc_now_iso

logger = logging.getLogger(__name__)

class EventBroadcaster:
    """
    In-process Event Broadcaster for Server-Sent Events (SSE).
    Distributes real-time audit, assessment, and evidence events to active frontend listeners.
    
    Architectural Note:
    This broadcaster is designed for a single-process local backend instance.
    For multi-instance distributed deployments, an external message broker
    (e.g., Redis Pub/Sub, AWS SQS/SNS) would replace this in-memory queue hub.
    """

    def __init__(self, history_size: int = 100):
        self._subscribers: Set[asyncio.Queue] = set()
        self._history: deque = deque(maxlen=history_size)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def get_recent_events(self, limit: int = 25) -> List[Dict[str, Any]]:
        return list(self._history)[-limit:]

    async def subscribe(self, initial_events: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[ServerSentEvent, None]:
        # Snapshot historical events before subscribing queue to prevent duplicates
        replay = list(initial_events) if initial_events is not None else list(self._history)

        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subscribers.add(queue)
        logger.info("New SSE client subscribed. Active listeners: %d", len(self._subscribers))

        try:
            # 1. Send initial connection established event
            conn_event = {
                "event_id": f"conn-{uuid.uuid4().hex[:8]}",
                "event_type": "CONNECTION_ESTABLISHED",
                "type": "CONNECTION_ESTABLISHED",
                "occurred_at": utc_now_iso(),
                "timestamp": utc_now_iso(),
                "actor": "system",
                "summary": "Established secure live SSE telemetry stream with BuildTrust AI backend.",
                "reason_codes": ["SSE_STREAM_INITIALIZED"],
                "is_demo": False,
                "details": {"active_subscribers": len(self._subscribers)}
            }
            yield ServerSentEvent(data=json.dumps(conn_event))

            # 2. Replay historical events captured before subscription
            for evt in replay[-25:]:
                yield ServerSentEvent(data=json.dumps(evt))

            # 3. Main event loop with 15-second heartbeat keep-alive
            while True:
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield ServerSentEvent(data=json.dumps(event_data))
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment to prevent proxy or browser timeout
                    yield ServerSentEvent(comment="heartbeat")

        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            self._subscribers.discard(queue)
            logger.info("SSE client disconnected. Active listeners: %d", len(self._subscribers))

    async def broadcast(self, event_data: Dict[str, Any]):
        """Publish event to history ring buffer and all connected subscriber queues asynchronously."""
        now = utc_now_iso()
        event_data.setdefault("event_id", f"evt-{uuid.uuid4().hex[:8]}")
        event_data.setdefault("occurred_at", event_data.get("timestamp", now))
        event_data.setdefault("timestamp", event_data["occurred_at"])
        event_data.setdefault("type", event_data.get("event_type", "AUDIT_EVENT"))
        event_data.setdefault("event_type", event_data["type"])
        event_data.setdefault("actor", "system")
        event_data.setdefault("reason_codes", [])
        event_data.setdefault("summary", f"{event_data.get('event_type')} processed.")
        event_data.setdefault("is_demo", False)

        # Store in recent history
        self._history.append(event_data)

        if not self._subscribers:
            return

        dead_queues = set()
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event_data)
            except asyncio.QueueFull:
                logger.warning("Subscriber queue full. Discarding slow subscriber.")
                dead_queues.add(queue)
            except Exception:
                dead_queues.add(queue)

        for q in dead_queues:
            self._subscribers.discard(q)

broadcaster = EventBroadcaster()
