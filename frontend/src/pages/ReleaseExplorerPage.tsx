import React, { useState } from 'react';
import { Release, DecisionType } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ScoreGauge } from '../components/ScoreGauge';
import { Search, Filter, Layers, ExternalLink } from 'lucide-react';

interface Props {
  releases: Release[];
  onSelectRelease: (releaseId: string) => void;
}

export const ReleaseExplorerPage: React.FC<Props> = ({ releases, onSelectRelease }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredReleases = releases.filter((rel) => {
    const matchesSearch = 
      rel.release_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rel.project_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rel.version.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || rel.latest_decision === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Release Candidate Explorer</h2>
          <p className="text-xs text-slate-400">Search and inspect all verified software release candidates</p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {/* Search */}
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search release or project..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          {/* Filter */}
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-emerald-500/50 cursor-pointer"
            >
              <option value="ALL">All Statuses</option>
              <option value="APPROVE">APPROVE</option>
              <option value="REVIEW">REVIEW</option>
              <option value="BLOCK">BLOCK</option>
              <option value="INSUFFICIENT_EVIDENCE">INSUFFICIENT EVIDENCE</option>
            </select>
          </div>
        </div>
      </div>

      {/* Release Candidates Table */}
      <div className="rounded-2xl bg-slate-900/40 border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] text-slate-400 uppercase bg-slate-900/80 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Release ID</th>
                <th className="py-3 px-4">Project</th>
                <th className="py-3 px-4">Version</th>
                <th className="py-3 px-4">Source Commit</th>
                <th className="py-3 px-4">Environment</th>
                <th className="py-3 px-4">Trust Score</th>
                <th className="py-3 px-4">Decision</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filteredReleases.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500 text-xs">
                    No release candidates match your search or filter criteria.
                  </td>
                </tr>
              ) : (
                filteredReleases.map((rel) => (
                  <tr key={rel.release_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-medium text-slate-200">
                      <div className="flex items-center gap-2">
                        <Layers className="w-3.5 h-3.5 text-slate-500" />
                        <span>{rel.release_id}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-300">{rel.project_id}</td>
                    <td className="py-3.5 px-4 font-mono text-slate-400">{rel.version}</td>
                    <td className="py-3.5 px-4 font-mono text-slate-500">{rel.source_commit.substring(0, 8)}</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono bg-slate-800 text-slate-300 border border-slate-700">
                        {rel.environment}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <ScoreGauge score={rel.latest_trust_score} size="sm" />
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge decision={rel.latest_decision} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => onSelectRelease(rel.release_id)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 text-xs font-semibold border border-emerald-500/30 transition-colors cursor-pointer"
                      >
                        <span>Inspect</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
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
