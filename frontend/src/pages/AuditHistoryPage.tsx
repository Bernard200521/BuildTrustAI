import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { AuditEvent } from '../types';
import { History, Shield, Search, RefreshCw } from 'lucide-react';

interface Props {
  initialEvents: AuditEvent[];
}

export const AuditHistoryPage: React.FC<Props> = ({ initialEvents }) => {
  const [events, setEvents] = useState<AuditEvent[]>(initialEvents);
  const [loading, setLoading] = useState<boolean>(false);
  const [search, setSearch] = useState<string>('');

  const loadAudits = async () => {
    setLoading(true);
    try {
      const list = await api.getAuditEvents();
      setEvents(list);
    } catch (err) {
      console.error('Failed to load audit history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudits();
  }, []);

  const filtered = events.filter((e) => 
    e.event_type.toLowerCase().includes(search.toLowerCase()) ||
    e.release_id.toLowerCase().includes(search.toLowerCase()) ||
    e.project_id.toLowerCase().includes(search.toLowerCase()) ||
    e.actor.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white">Immutable Audit Trail</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
              AUDIT COMPLIANCE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Complete, timestamped log of evidence arrivals, trust score shifts, and release gate decision events.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search audit trail..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none"
            />
          </div>

          <button
            onClick={loadAudits}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Audit Table */}
      <div className="rounded-2xl bg-slate-900/40 border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Release ID</th>
                <th className="py-3 px-4">Transition</th>
                <th className="py-3 px-4">Reason Codes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans text-xs">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    No audit records found.
                  </td>
                </tr>
              ) : (
                filtered.map((evt) => (
                  <tr key={evt.event_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-400">{evt.event_id}</td>
                    <td className="py-3 px-4 text-slate-400 text-[11px] font-mono">
                      {new Date(evt.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-emerald-400 border border-slate-700">
                        {evt.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">{evt.actor}</td>
                    <td className="py-3 px-4 font-mono text-slate-200 font-semibold">{evt.release_id}</td>
                    <td className="py-3 px-4">
                      {evt.previous_decision || evt.new_decision ? (
                        <span className="text-[11px] font-mono">
                          <span className="text-slate-500">{evt.previous_decision || 'INIT'}</span>
                          <span className="text-slate-600 mx-1">→</span>
                          <span className="text-slate-200 font-bold">{evt.new_decision}</span>
                        </span>
                      ) : (
                        <span className="text-slate-600 font-mono text-[11px]">--</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {evt.reason_codes?.map((code, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-slate-800 text-slate-400 border border-slate-700"
                          >
                            {code}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
