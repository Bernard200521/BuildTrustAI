import React from 'react';
import { DashboardSummary, Release } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ScoreGauge } from '../components/ScoreGauge';
import { 
  FolderGit2, 
  Layers, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Gauge,
  ArrowRight,
  TrendingUp,
  ShieldAlert,
  Activity,
  Zap,
  Radio,
  FileQuestion
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  PieChart,
  Pie,
  AreaChart,
  Area,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis
} from 'recharts';

interface Props {
  summary: DashboardSummary | null;
  loading: boolean;
  onSelectRelease: (releaseId: string) => void;
  onNavigateExplorer: () => void;
}

export const OverviewPage: React.FC<Props> = ({ summary, loading, onSelectRelease, onNavigateExplorer }) => {
  if (loading || !summary) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-2 border-emerald-500/20 border-t-emerald-500 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
          </div>
        </div>
        <span className="text-xs font-mono text-slate-400">Connecting to ECTE Live Telemetry Feed...</span>
      </div>
    );
  }

  const { metrics, vulnerability_distribution, recent_releases, recent_events } = summary;

  // Chart 1: Vulnerability Severity Spectrum
  const vulnData = [
    { name: 'Critical', count: vulnerability_distribution.CRITICAL, color: '#f43f5e' },
    { name: 'High', count: vulnerability_distribution.HIGH, color: '#f97316' },
    { name: 'Medium', count: vulnerability_distribution.MEDIUM, color: '#eab308' },
    { name: 'Low', count: vulnerability_distribution.LOW, color: '#06b6d4' },
  ];

  // Chart 2: Release Gate Decisions Donut
  const decisionData = [
    { name: 'Approved', value: metrics.approved_releases, color: '#10b981' },
    { name: 'Review', value: metrics.review_releases, color: '#f59e0b' },
    { name: 'Blocked', value: metrics.blocked_releases, color: '#ef4444' },
    { name: 'Insufficient Evidence', value: metrics.insufficient_evidence_releases ?? metrics.pending_releases, color: '#6366f1' },
  ].filter(d => d.value > 0);

  // Chart 3: Continuous Trust Score Timeline (Simulated or Real Event History)
  const timelineData = recent_releases.map((rel, idx) => ({
    release: rel.release_id.replace('rel-', ''),
    trustScore: rel.latest_trust_score || 0,
    time: new Date(rel.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  })).reverse();

  // Chart 4: Multi-Vector Defense Posture Radar Chart (Integrity, Dependency, Provenance, Tests, Completeness)
  const radarData = [
    { subject: 'Artifact Integrity', score: 98, fullMark: 100 },
    { subject: 'Dependency Health', score: 78, fullMark: 100 },
    { subject: 'SLSA Provenance', score: 88, fullMark: 100 },
    { subject: 'Security Tests', score: 92, fullMark: 100 },
    { subject: 'Evidence Completeness', score: 85, fullMark: 100 },
  ];

  return (
    <div className="space-y-6">
      {/* Live Telemetry Ticker Banner */}
      <div className="p-3 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900/80 to-cyan-950/40 border border-emerald-500/20 shadow-lg flex items-center justify-between text-xs overflow-hidden">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-[10px] font-bold">
            <Zap className="w-3 h-3 text-emerald-400 animate-pulse" />
            <span>REAL-TIME TELEMETRY</span>
          </div>
          <span className="text-slate-300 font-mono text-[11px] truncate">
            {recent_events[0] ? (
              <>
                Latest Event: <strong className="text-white">{recent_events[0].event_type}</strong> on <span className="text-emerald-400 font-bold">{recent_events[0].release_id}</span> ({new Date(recent_events[0].timestamp).toLocaleTimeString()})
              </>
            ) : (
              'Continuous trust verification active. Monitoring software supply chain events.'
            )}
          </span>
        </div>
        <div className="hidden sm:flex items-center gap-2 font-mono text-[11px] text-slate-400">
          <span>ECTE Formula Active</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        </div>
      </div>

      {/* Metric Cards Grid - 7 Columns */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all shadow-xl backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Projects</span>
            <FolderGit2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black font-mono text-white">{metrics.total_projects}</div>
          <div className="text-[10px] text-slate-400 mt-1">Monitored services</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all shadow-xl backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Releases</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black font-mono text-white">{metrics.total_releases}</div>
          <div className="text-[10px] text-slate-400 mt-1">Evaluated candidates</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-emerald-500/20 hover:border-emerald-500/40 transition-all shadow-xl backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium text-emerald-400">Approved</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black font-mono text-emerald-400">{metrics.approved_releases}</div>
          <div className="text-[10px] text-emerald-500/70 mt-1">Cleared for promotion</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-amber-500/20 hover:border-amber-500/40 transition-all shadow-xl backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium text-amber-400">Under Review</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black font-mono text-amber-400">{metrics.review_releases}</div>
          <div className="text-[10px] text-amber-500/70 mt-1">SecOps attention</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-rose-500/20 hover:border-rose-500/40 transition-all shadow-xl backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium text-rose-400">Policy Blocked</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black font-mono text-rose-400">{metrics.blocked_releases}</div>
          <div className="text-[10px] text-rose-500/70 mt-1">Mandatory gate stops</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-indigo-500/20 hover:border-indigo-500/40 transition-all shadow-xl backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium text-indigo-400">Insufficient Evid.</span>
            <FileQuestion className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-black font-mono text-indigo-400">
            {metrics.insufficient_evidence_releases ?? metrics.pending_releases}
          </div>
          <div className="text-[10px] text-indigo-400/70 mt-1">Missing artifacts/scans</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-teal-500/20 hover:border-teal-500/40 transition-all shadow-xl backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium text-teal-400">Avg Trust Index</span>
            <Gauge className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-black font-mono text-teal-300">{metrics.average_trust_score.toFixed(1)}</div>
          <div className="text-[10px] text-teal-500/70 mt-1">Composite score T</div>
        </div>
      </div>

      {/* Charts Row 1: Radar Posture & Trust Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar Chart: Multi-Vector Defense Posture */}
        <div className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800/80 shadow-2xl backdrop-blur-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                Multi-Vector Defense Posture (ECTE Balance)
              </h3>
              <span className="text-[10px] font-mono text-cyan-400 font-semibold px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                RADAR MATRIX
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Balance across Integrity (I), Dependency (D), Provenance (P), Tests (S), and Completeness (E)
            </p>
          </div>

          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" stroke="#94a3b8" tick={{ fontSize: 10, fill: '#cbd5e1' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#475569" tick={{ fontSize: 9 }} />
                <Radar 
                  name="Posture Score" 
                  dataKey="score" 
                  stroke="#06b6d4" 
                  fill="#06b6d4" 
                  fillOpacity={0.3} 
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#090e17', borderColor: '#1e293b', borderRadius: '12px', fontSize: '11px' }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Area Chart: Continuous Release Trust Timeline */}
        <div className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800/80 shadow-2xl backdrop-blur-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                Release Trust Index Timeline
              </h3>
              <span className="text-[10px] font-mono text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                CONTINUOUS FEED
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Real-time trust score fluctuations across candidate releases
            </p>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timelineData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="trustScoreGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="release" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#090e17', borderColor: '#1e293b', borderRadius: '12px', fontSize: '12px' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="trustScore" 
                  stroke="#10b981" 
                  strokeWidth={2.5}
                  fillOpacity={1} 
                  fill="url(#trustScoreGradient)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Charts Row 2: Vulnerabilities Spectrum & Gate Decisions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vulnerability Severity Spectrum */}
        <div className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800/80 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rose-400" />
              Dependency Vulnerability Severity Spectrum
            </h3>
            <span className="text-[10px] font-mono text-slate-400">OSV.dev Normalized</span>
          </div>
          <p className="text-xs text-slate-400 mb-4">Deduplicated vulnerability advisories across all release candidates</p>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={vulnData} layout="vertical" margin={{ top: 5, right: 30, left: 15, bottom: 5 }}>
                <XAxis type="number" stroke="#64748b" fontSize={11} allowDecimals={false} />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#090e17', borderColor: '#1e293b', borderRadius: '12px', fontSize: '12px' }}
                  cursor={{ fill: '#1e293b' }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                  {vulnData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Gate Decisions Donut */}
        <div className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800/80 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              Release Gate Decision Breakdown
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Policy Controlled</span>
          </div>
          <p className="text-xs text-slate-400 mb-4">Current release distribution across deterministic gate outcomes</p>

          <div className="h-56 flex items-center justify-center">
            {decisionData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={decisionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                    fontSize={11}
                  >
                    {decisionData.map((entry, index) => (
                      <Cell key={`cell-pie-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#090e17', borderColor: '#1e293b', borderRadius: '12px', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-500">No release data available</div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Releases & Live Activity Table */}
      <div className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800/80 shadow-2xl backdrop-blur-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white">Active Release Candidates</h3>
            <p className="text-xs text-slate-400">Inspect evaluated software releases and policy gate decisions</p>
          </div>
          <button
            onClick={onNavigateExplorer}
            className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-semibold cursor-pointer"
          >
            <span>View Full Explorer</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] text-slate-400 uppercase bg-slate-950/60 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Release ID</th>
                <th className="py-3 px-4">Project</th>
                <th className="py-3 px-4">Version</th>
                <th className="py-3 px-4">Trust Score</th>
                <th className="py-3 px-4">Decision</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {recent_releases.map((rel) => (
                <tr key={rel.release_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-medium text-slate-200">
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      {rel.release_id}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300 font-semibold">{rel.project_id}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-400">{rel.version}</td>
                  <td className="py-3.5 px-4">
                    <ScoreGauge score={rel.latest_trust_score} size="sm" />
                  </td>
                  <td className="py-3.5 px-4">
                    <StatusBadge decision={rel.latest_decision} size="sm" />
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => onSelectRelease(rel.release_id)}
                      className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors cursor-pointer"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
