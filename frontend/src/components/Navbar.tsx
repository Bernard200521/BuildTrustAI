import React, { useState } from 'react';
import { 
  Shield, 
  Activity, 
  Sparkles, 
  User, 
  Play, 
  Pause, 
  Bell, 
  Search, 
  Plus, 
  CheckCircle2, 
  ExternalLink,
  ChevronDown,
  Server
} from 'lucide-react';
import { ConnectionStatus } from '../hooks/useLiveEvents';
import { api } from '../api/client';

import iconSvg from '../assets/icon.svg';

interface Props {
  connectionStatus: ConnectionStatus;
  onOpenDemoModal: () => void;
  onSelectTab: (tab: any) => void;
  currentTab: string;
}

export const Navbar: React.FC<Props> = ({ 
  connectionStatus, 
  onOpenDemoModal,
  onSelectTab,
  currentTab
}) => {
  const [streamActive, setStreamActive] = useState<boolean>(true);
  const [environment, setEnvironment] = useState<string>('staging');
  const [envOpen, setEnvOpen] = useState<boolean>(false);
  const [ticking, setTicking] = useState<boolean>(false);

  const toggleStream = async () => {
    if (streamActive) {
      await api.stopSimulator().catch(() => {});
      setStreamActive(false);
    } else {
      await api.startSimulator(6.0).catch(() => {});
      setStreamActive(true);
    }
  };

  const handleInstantPulse = async () => {
    setTicking(true);
    try {
      await api.triggerSimulatorTick();
    } catch (e) {
      console.error(e);
    } finally {
      setTimeout(() => setTicking(false), 500);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-5 flex items-center justify-between sticky top-0 z-40 shadow-xl">
      {/* Left: Brand Identity & Breadcrumbs */}
      <div className="flex items-center gap-4">
        <div 
          onClick={() => onSelectTab('overview')}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="relative p-1.5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg shadow-emerald-500/10 group-hover:border-emerald-500/40 transition-all">
            <img src={iconSvg} alt="BuildTrust AI Shield Logo" className="w-6 h-6 object-contain" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base tracking-tight text-white group-hover:text-emerald-400 transition-colors">
                Build<span className="text-cyan-400">Trust</span> <span className="text-emerald-400 font-mono text-xs px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30">AI</span>
              </span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase bg-slate-800 text-slate-300 border border-slate-700">
                ECTE v1.0
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium hidden sm:block">Continuous Release Trust Gate</p>
          </div>
        </div>

        {/* Environment Badge */}
        <div className="relative hidden md:block">
          <button 
            onClick={() => setEnvOpen(!envOpen)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300 hover:border-slate-700 transition-colors"
          >
            <Server className="w-3 h-3 text-emerald-400" />
            <span className="uppercase font-semibold">{environment}</span>
            <ChevronDown className="w-3 h-3 text-slate-500" />
          </button>
          {envOpen && (
            <div className="absolute top-8 left-0 w-36 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-1 z-50 text-xs">
              <button 
                onClick={() => { setEnvironment('staging'); setEnvOpen(false); }}
                className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-200"
              >
                staging
              </button>
              <button 
                onClick={() => { setEnvironment('production'); setEnvOpen(false); }}
                className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-200"
              >
                production
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Center: Live Telemetry & Streaming Controls */}
      <div className="hidden lg:flex items-center gap-3">
        {/* Live Streaming Toggle */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/90 border border-slate-800/90 shadow-inner">
          <span className="relative flex h-2.5 w-2.5">
            {streamActive ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-slate-600"></span>
            )}
          </span>
          <span className="text-[11px] font-mono text-slate-300">
            {streamActive ? 'TELEMETRY STREAM: LIVE' : 'STREAM: PAUSED'}
          </span>
          <button
            onClick={toggleStream}
            className="p-1 rounded-full hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title={streamActive ? 'Pause real-time stream' : 'Resume real-time stream'}
          >
            {streamActive ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3 text-emerald-400" />}
          </button>
        </div>

        {/* Pulse button */}
        <button
          onClick={handleInstantPulse}
          disabled={ticking}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-300 hover:text-emerald-400 font-mono transition-all cursor-pointer"
          title="Emit immediate security verification event"
        >
          <Activity className={`w-3.5 h-3.5 text-cyan-400 ${ticking ? 'animate-spin' : ''}`} />
          <span>Instant Pulse</span>
        </button>
      </div>

      {/* Right: Actions & User Account */}
      <div className="flex items-center gap-3">
        {/* Scenarios Modal Trigger */}
        <button
          onClick={onOpenDemoModal}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/50 transition-all cursor-pointer"
        >
          <Sparkles className="w-3.5 h-3.5 text-emerald-200" />
          <span>Interactive Scenarios</span>
        </button>

        {/* User Account Pill */}
        <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-slate-800 to-slate-700 border border-slate-600 flex items-center justify-center text-slate-200 shadow-md">
            <User className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-semibold text-slate-200 leading-tight">SecOps Admin</div>
            <div className="text-[10px] font-mono text-emerald-400">ADMIN ROLE</div>
          </div>
        </div>
      </div>
    </header>
  );
};
