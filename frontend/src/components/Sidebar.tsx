import React from 'react';
import { 
  LayoutDashboard, 
  Layers, 
  FileCheck2, 
  Activity, 
  BrainCircuit, 
  History, 
  ShieldAlert,
  ChevronRight,
  ShieldCheck,
  Radio
} from 'lucide-react';
import { Release } from '../types';

export type TabType = 
  | 'overview' 
  | 'explorer' 
  | 'details' 
  | 'events' 
  | 'ai' 
  | 'audit' 
  | 'settings';

interface Props {
  currentTab: TabType;
  onSelectTab: (tab: TabType) => void;
  releases?: Release[];
}

export const Sidebar: React.FC<Props> = ({ currentTab, onSelectTab, releases = [] }) => {
  const blockedCount = releases.filter(r => r.latest_decision === 'BLOCK').length;
  const reviewCount = releases.filter(r => r.latest_decision === 'REVIEW').length;
  const approvedCount = releases.filter(r => r.latest_decision === 'APPROVE').length;
  const insufficientCount = releases.filter(r => r.latest_decision === 'INSUFFICIENT_EVIDENCE' || r.latest_decision === 'PENDING_ASSESSMENT').length;

  const navItems = [
    { 
      id: 'overview', 
      label: 'Security Overview', 
      icon: LayoutDashboard,
      badge: 'Live'
    },
    { 
      id: 'explorer', 
      label: 'Release Explorer', 
      icon: Layers,
      badge: releases.length ? `${releases.length}` : undefined
    },
    { 
      id: 'details', 
      label: 'Release Verification', 
      icon: FileCheck2,
      badge: blockedCount > 0 ? `${blockedCount} Blocked` : undefined,
      badgeColor: 'rose'
    },
    { 
      id: 'events', 
      label: 'Live Telemetry Feed', 
      icon: Activity,
      badge: 'SSE Active',
      badgeColor: 'emerald'
    },
    { 
      id: 'ai', 
      label: 'AI Risk Prioritization', 
      icon: BrainCircuit,
      badge: 'ML Engine'
    },
    { 
      id: 'audit', 
      label: 'Immutable Audit Trail', 
      icon: History 
    },
    { 
      id: 'settings', 
      label: 'Policy Gate Config', 
      icon: ShieldAlert 
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950/60 backdrop-blur-xl flex flex-col justify-between p-4 shrink-0 shadow-2xl">
      <div>
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-3 flex items-center justify-between">
          <span>Security Navigation</span>
          <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
        </div>
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id as TabType)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer group ${
                  isActive
                    ? 'bg-gradient-to-r from-emerald-500/15 to-teal-500/5 text-emerald-400 border border-emerald-500/30 shadow-lg shadow-emerald-950/40'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-emerald-400' : 'text-slate-500 group-hover:text-slate-300'
                  }`} />
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                    item.badgeColor === 'rose'
                      ? 'bg-rose-950/80 text-rose-400 border border-rose-500/30'
                      : item.badgeColor === 'emerald'
                      ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-500/30'
                      : 'bg-slate-900 text-slate-400 border border-slate-800'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Release Posture Snapshot Card */}
      <div className="p-3.5 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-slate-800/80 shadow-inner text-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-bold text-slate-200">Release Gate Posture</span>
          <span className="text-[10px] font-mono text-emerald-400">Continuous</span>
        </div>
        
        <div className="space-y-1.5 text-[11px] font-mono">
          <div className="flex justify-between items-center text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Approved
            </span>
            <span className="text-emerald-400 font-bold">{approvedCount}</span>
          </div>
          <div className="flex justify-between items-center text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Under Review
            </span>
            <span className="text-amber-400 font-bold">{reviewCount}</span>
          </div>
          <div className="flex justify-between items-center text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
              Policy Blocked
            </span>
            <span className="text-rose-400 font-bold">{blockedCount}</span>
          </div>
          <div className="flex justify-between items-center text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              Insufficient Evid.
            </span>
            <span className="text-indigo-400 font-bold">{insufficientCount}</span>
          </div>
        </div>

        <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400 font-mono">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            LOCAL STORAGE
          </span>
          <span className="text-emerald-400 font-bold">ACTIVE</span>
        </div>
      </div>
    </aside>
  );
};
