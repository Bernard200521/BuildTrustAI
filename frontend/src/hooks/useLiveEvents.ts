import { useEffect, useState, useRef, useCallback } from 'react';

export type ConnectionStatus = 'connected' | 'reconnecting' | 'disconnected';

export interface UseLiveEventsResult {
  status: ConnectionStatus;
  events: any[];
  isPaused: boolean;
  togglePause: () => void;
  reconnect: () => void;
  clearEvents: () => void;
  lastReceivedAt: string | null;
  errorMessage: string | null;
}

export function useLiveEvents(onEventReceived?: (event: any) => void): UseLiveEventsResult {
  const [status, setStatus] = useState<ConnectionStatus>('reconnecting');
  const [events, setEvents] = useState<any[]>([]);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [lastReceivedAt, setLastReceivedAt] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const seenEventIdsRef = useRef<Set<string>>(new Set());
  const isPausedRef = useRef<boolean>(false);
  isPausedRef.current = isPaused;

  const onEventReceivedRef = useRef(onEventReceived);
  onEventReceivedRef.current = onEventReceived;

  const connectSSE = useCallback(() => {
    // Clean up existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setStatus('reconnecting');
    setErrorMessage(null);

    try {
      const es = new EventSource('/api/v1/events');
      eventSourceRef.current = es;

      es.onopen = () => {
        setStatus('connected');
        setErrorMessage(null);
      };

      es.onmessage = (e) => {
        try {
          if (!e.data || e.data.trim() === '') return;
          const data = JSON.parse(e.data);

          // Track event timestamp
          const nowIso = new Date().toISOString();
          setLastReceivedAt(data.occurred_at || data.timestamp || nowIso);

          // Deduplication check by event_id
          const eventId = data.event_id || `${data.type}-${data.timestamp}-${Math.random()}`;
          if (seenEventIdsRef.current.has(eventId)) {
            return;
          }
          seenEventIdsRef.current.add(eventId);

          // Ignore purely internal heartbeat payloads for UI list, but keep connection active
          if (data.event_type === 'CONNECTION_ESTABLISHED') {
            setStatus('connected');
          }

          if (!isPausedRef.current) {
            setEvents((prev) => [data, ...prev.slice(0, 99)]);
          }

          if (onEventReceivedRef.current) {
            onEventReceivedRef.current(data);
          }
        } catch (err: any) {
          console.error('Failed to parse SSE event payload:', err, e.data);
        }
      };

      es.onerror = () => {
        setStatus('disconnected');
        setErrorMessage('Unable to connect to FastAPI SSE stream at /api/v1/events. Ensure backend server is running on port 8000.');
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }

        // Schedule reconnection attempt in 4 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectSSE();
        }, 4000);
      };
    } catch (err: any) {
      setStatus('disconnected');
      setErrorMessage(`SSE connection initialization error: ${err?.message || 'Failed'}`);
    }
  }, []);

  useEffect(() => {
    connectSSE();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [connectSSE]);

  const togglePause = useCallback(() => {
    setIsPaused((prev) => !prev);
  }, []);

  const reconnect = useCallback(() => {
    connectSSE();
  }, [connectSSE]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    seenEventIdsRef.current.clear();
  }, []);

  return {
    status,
    events,
    isPaused,
    togglePause,
    reconnect,
    clearEvents,
    lastReceivedAt,
    errorMessage
  };
}
