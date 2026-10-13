import React, { useState } from 'react';
import { ConnectionStatus } from '../hooks/useLiveEvents';
import { 
  Activity, 
  Search, 
  Filter, 
  Pause, 
  Play, 
  RotateCcw, 
  Trash2, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  Sparkles,
  Wifi,
  WifiOff
} from 'lucide-react';

interface Props {
  events: any[];
  connectionStatus: ConnectionStatus;
  isPaused?: boolean;
  onTogglePause?: () => void;
  onReconnect?: () => void;
  onClearEvents?: () => void;
  lastReceivedAt?: string | null;
  errorMessage?: string | null;
  onOpenDemoModal: () => void;
}

export const LiveEventMonitorPage: React.FC<Props> = ({ 
  events, 
  connectionStatus, 
  isPaused = false,
  onTogglePause,
  onReconnect,
  onClearEvents,
  lastReceivedAt,
  errorMessage,
  onOpenDemoModal 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [releaseFilter, setReleaseFilter] = useState('ALL');

  // Extract unique release IDs from events
  const uniqueReleases = Array.from(new Set(events.map(e => e.release_id).filter(Boolean)));
  const uniqueTypes = Array.from(new Set(events.map(e => e.event_type || e.type).filter(Boolean)));

  const filteredEvents = events.filter((evt) => {
    const evType = (evt.event_type || evt.type || '').toUpperCase();
    const relId = evt.release_id || '';
    const actor = evt.actor || '';
    const summary = evt.summary || '';
    const searchLower = searchTerm.toLowerCase();

    const matchesSearch = 
      !searchTerm ||
      evType.toLowerCase().includes(searchLower) ||
      relId.toLowerCase().includes(searchLower) ||
      actor.toLowerCase().includes(searchLower) ||
      summary.toLowerCase().includes(searchLower);

    const matchesType = typeFilter === 'ALL' || evType === typeFilter;
    const matchesRelease = releaseFilter === 'ALL' || relId === releaseFilter;

    return matchesSearch && matchesType && matchesRelease;
  });

  return (
    <div className="space-y-6">
      {/* Header & Connection Telemetry Status */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-xl font-bold text-white">Live Event Monitor</h2>
            <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono border ${
              connectionStatus === 'connected' 
                ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-400' 
                : connectionStatus === 'reconnecting' 
                ? 'bg-amber-950/60 border-amber-500/30 text-amber-400' 
                : 'bg-rose-950/60 border-rose-500/30 text-rose-400'
            }`}>
              <span className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected' 
                  ? 'bg-emerald-400 animate-pulse' 
                  : connectionStatus === 'reconnecting' 
                  ? 'bg-amber-400 animate-ping' 
                  : 'bg-rose-400'
              }`} />
              <span className="font-semibold tracking-wide uppercase text-[10px]">
                {connectionStatus === 'connected' 
                  ? 'CONNECTED (SSE ACTIVE)' 
                  : connectionStatus === 'reconnecting' 
                  ? 'RECONNECTING...' 
                  : 'DISCONNECTED'}
              </span>
            </div>
            {isPaused && (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30">
                STREAM PAUSED
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time feed of evidence ingestions, ECTE delta assessments, policy gating outcomes, and audit records.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {onTogglePause && (
            <button
              onClick={onTogglePause}
              className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
                isPaused 
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-500' 
                  : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border-slate-800'
              }`}
              title={isPaused ? 'Resume live incoming event feed' : 'Pause incoming live feed'}
            >
              {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
              <span>{isPaused ? 'Resume Feed' : 'Pause'}</span>
            </button>
          )}

          {onReconnect && (
            <button
              onClick={onReconnect}
              className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
              title="Manually reconnect to SSE stream"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reconnect</span>
            </button>
          )}

          {onClearEvents && (
            <button
              onClick={onClearEvents}
              disabled={events.length === 0}
              className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-slate-400 hover:text-rose-400 border border-slate-800 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
              title="Clear event feed view"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          )}

          <button
            onClick={onOpenDemoModal}
            className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-lg shadow-emerald-950/40"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-200" />
            <span>Simulate Events</span>
          </button>
        </div>
      </div>

      {/* Backend Unavailable Error Banner */}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-center justify-between text-xs text-rose-300">
          <div className="flex items-center gap-2.5">
            <WifiOff className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          {onReconnect && (
            <button
              onClick={onReconnect}
              className="px-2.5 py-1 rounded bg-rose-900/60 hover:bg-rose-900 text-white text-[11px] font-semibold border border-rose-500/40 transition-colors"
            >
              Retry Connection
            </button>
          )}
        </div>
      )}

      {/* Filter and Telemetry Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Search */}
          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search by event, release, actor..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/50 font-mono"
            />
          </div>

          {/* Type Filter */}
          <div className="relative">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-emerald-500/50 cursor-pointer font-mono"
            >
              <option value="ALL">All Event Types ({events.length})</option>
              {uniqueTypes.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* Release Filter */}
          {uniqueReleases.length > 0 && (
            <div className="relative">
              <select
                value={releaseFilter}
                onChange={(e) => setReleaseFilter(e.target.value)}
                className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-emerald-500/50 cursor-pointer font-mono"
              >
                <option value="ALL">All Releases</option>
                {uniqueReleases.map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Telemetry info */}
        <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400 shrink-0">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-cyan-400" />
            <span>Last Event:</span>
            <span className="text-slate-200 font-semibold">
              {lastReceivedAt ? new Date(lastReceivedAt).toLocaleTimeString() : 'Awaiting'}
            </span>
          </div>
          <span>•</span>
          <div>
            Showing <strong className="text-white">{filteredEvents.length}</strong> of {events.length}
          </div>
        </div>
      </div>

      {/* Events Stream Feed */}
      <div className="rounded-2xl bg-slate-900/40 border border-slate-800 p-4">
        {filteredEvents.length === 0 ? (
          <div className="text-center py-16 text-slate-500 text-xs">
            <Activity className="w-8 h-8 mx-auto mb-2 opacity-40 animate-pulse text-emerald-400" />
            <p className="font-semibold text-slate-400">
              {events.length === 0 
                ? 'Listening for real-time SSE stream events from the FastAPI backend...' 
                : 'No events match the selected filters.'}
            </p>
            <p className="text-[11px] text-slate-600 mt-1">
              Trigger an interactive scenario or submit new security evidence to observe live delta updates.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredEvents.map((evt, idx) => {
              const eventType = evt.event_type || evt.type || 'EVENT';
              const isDemo = evt.is_demo === true || 
                (evt.actor && (evt.actor.includes('demo') || evt.actor.includes('scenario')));
              const isBlock = evt.decision === 'BLOCK' || eventType === 'POLICY_BLOCKED';
              const isApprove = evt.decision === 'APPROVE' || eventType === 'RELEASE_APPROVED';

              return (
                <div
                  key={evt.event_id || idx}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 hover:border-slate-700 transition-all text-xs font-mono shadow-md"
                >
                  {/* Top Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-2">
                      {/* Event Type Pill */}
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold border ${
                        isBlock 
                          ? 'bg-rose-950/80 text-rose-400 border-rose-500/40' 
                          : isApprove 
                          ? 'bg-emerald-950/80 text-emerald-400 border-emerald-500/40' 
                          : 'bg-cyan-950/80 text-cyan-400 border-cyan-500/40'
                      }`}>
                        {eventType}
                      </span>

                      {/* Release ID */}
                      {evt.release_id && (
                        <span className="text-slate-200 font-bold">{evt.release_id}</span>
                      )}

                      {/* Project ID */}
                      {evt.project_id && (
                        <span className="text-slate-500 text-[11px]">({evt.project_id})</span>
                      )}

                      {/* Demo vs Production Label */}
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-semibold border ${
                        isDemo 
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' 
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}>
                        {isDemo ? 'DEMO TEST' : 'REAL EVENT'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-slate-500 text-[11px]">
                      <span>{new Date(evt.occurred_at || evt.timestamp || Date.now()).toLocaleTimeString()}</span>
                      {evt.actor && (
                        <span className="text-slate-400 text-[10px]">&bull; {evt.actor}</span>
                      )}
                    </div>
                  </div>

                  {/* Summary */}
                  {evt.summary && (
                    <div className="text-slate-300 font-sans text-xs leading-relaxed mb-2.5">
                      {evt.summary}
                    </div>
                  )}

                  {/* Decision & Score Metrics */}
                  {evt.decision && (
                    <div className="flex flex-wrap items-center gap-3 my-2 pt-2 border-t border-slate-900 text-xs">
                      <span className="text-slate-400">Decision Outcome:</span>
                      <span className={`font-bold px-2 py-0.5 rounded text-xs ${
                        evt.decision === 'APPROVE' 
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' 
                          : evt.decision === 'BLOCK' 
                          ? 'bg-rose-950 text-rose-400 border border-rose-500/30' 
                          : 'bg-amber-950 text-amber-400 border border-amber-500/30'
                      }`}>
                        {evt.decision}
                      </span>

                      {evt.trust_score !== undefined && evt.trust_score !== null && (
                        <span className="text-slate-400">
                          Trust Score: <strong className="text-white font-mono">{evt.trust_score}</strong>
                        </span>
                      )}

                      {evt.assessment_version && (
                        <span className="text-slate-500 text-[11px]">
                          (Assessment #{evt.assessment_version})
                        </span>
                      )}
                    </div>
                  )}

                  {/* Reason Codes */}
                  {evt.reason_codes && evt.reason_codes.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-slate-900">
                      {evt.reason_codes.map((code: string, cIdx: number) => (
                        <span
                          key={cIdx}
                          className="px-2 py-0.5 rounded text-[10px] bg-slate-900 text-slate-300 border border-slate-800 flex items-center gap-1"
                        >
                          <ShieldAlert className="w-2.5 h-2.5 text-amber-400" />
                          <span>{code}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
