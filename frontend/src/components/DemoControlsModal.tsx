import React, { useState } from 'react';
import { api } from '../api/client';
import { X, Play, RefreshCw, ShieldCheck, AlertOctagon, FileWarning, HelpCircle, XCircle } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onTriggered: () => void;
  currentReleaseId?: string;
}

export const DemoControlsModal: React.FC<Props> = ({ 
  isOpen, 
  onClose, 
  onTriggered, 
  currentReleaseId = 'rel-payment-1.0.0' 
}) => {
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRun = async (scenarioKey: string, runner: () => Promise<any>, label: string) => {
    setLoadingScenario(scenarioKey);
    setStatusMessage(`Executing ${label}...`);
    try {
      const res = await runner();
      setStatusMessage(`Success: ${label} executed! New Decision: ${res.latest_decision || res.decision || 'Updated'} (Score: ${res.trust_score ?? res.latest_trust_score ?? 'N/A'})`);
      onTriggered();
    } catch (err: any) {
      setStatusMessage(`Execution error: ${err?.response?.data?.detail || err?.message || 'Failed'}`);
    } finally {
      setLoadingScenario(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-2">
          <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            DEMONSTRATION & TEST SUITE
          </span>
        </div>
        <h3 className="text-xl font-bold text-white mb-1">Evidence-Change Engine (ECTE) Scenarios</h3>
        <p className="text-xs text-slate-400 mb-5">
          Execute real backend verification workflows on <span className="font-mono text-emerald-400 font-semibold">{currentReleaseId}</span>. The server validates payloads, persists evidence, evaluates deterministic policy gates, and emits real-time SSE stream events.
        </p>

        {statusMessage && (
          <div className="mb-4 p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-emerald-300">
            {statusMessage}
          </div>
        )}

        <div className="space-y-2.5">
          {/* Scenario A: Trusted Release */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-emerald-500/40 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 mt-0.5">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white">Scenario A: Trusted Release Candidate</h4>
                <p className="text-[11px] text-slate-400">Complete valid evidence (matching hash, clean SBOM, clean vulns, SLSA prov, passed tests) &rarr; <span className="text-emerald-400 font-bold">APPROVE</span></p>
              </div>
            </div>
            <button
              disabled={loadingScenario !== null}
              onClick={() => handleRun('A', () => api.triggerScenarioA(currentReleaseId), 'Scenario A (Trusted Release)')}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {loadingScenario === 'A' ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Run
            </button>
          </div>

          {/* Scenario B: Artifact Tampering */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-amber-500/40 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 mt-0.5">
                <FileWarning className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white">Scenario B: Artifact Digest Tampering</h4>
                <p className="text-[11px] text-slate-400">Binary SHA-256 differs from expected digest. Deterministic integrity gate triggers immediate &rarr; <span className="text-rose-400 font-bold">BLOCK</span></p>
              </div>
            </div>
            <button
              disabled={loadingScenario !== null}
              onClick={() => handleRun('B', () => api.triggerScenarioB(currentReleaseId), 'Scenario B (Tampered Artifact)')}
              className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {loadingScenario === 'B' ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Run
            </button>
          </div>

          {/* Scenario C: Vulnerability Discovered */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-rose-500/40 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 mt-0.5">
                <AlertOctagon className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white">Scenario C: Vulnerability Discovered (Log4Shell CVE)</h4>
                <p className="text-[11px] text-slate-400">Injects verified CVSS 10.0 Log4j RCE finding. Zero-tolerance policy overrides score &rarr; <span className="text-rose-400 font-bold">BLOCK</span></p>
              </div>
            </div>
            <button
              disabled={loadingScenario !== null}
              onClick={() => handleRun('C', () => api.triggerScenarioC(currentReleaseId), 'Scenario C (Critical Vulnerability)')}
              className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {loadingScenario === 'C' ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Run
            </button>
          </div>

          {/* Scenario D: Missing Provenance */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-indigo-500/40 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 mt-0.5">
                <HelpCircle className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white">Scenario D: Missing Build Provenance</h4>
                <p className="text-[11px] text-slate-400">Artifact & scans present, but SLSA provenance omitted &rarr; <span className="text-indigo-400 font-bold">INSUFFICIENT EVIDENCE</span></p>
              </div>
            </div>
            <button
              disabled={loadingScenario !== null}
              onClick={() => handleRun('D', () => api.triggerScenarioD(currentReleaseId), 'Scenario D (Missing Provenance)')}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {loadingScenario === 'D' ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Run
            </button>
          </div>

          {/* Scenario E: Mandatory Test Failure */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-red-500/40 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-red-500/10 text-red-400 mt-0.5">
                <XCircle className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white">Scenario E: Mandatory Test Suite Failure</h4>
                <p className="text-[11px] text-slate-400">Failing security test results submitted. Mandatory gate condition breaches &rarr; <span className="text-rose-400 font-bold">BLOCK</span></p>
              </div>
            </div>
            <button
              disabled={loadingScenario !== null}
              onClick={() => handleRun('E', () => api.triggerScenarioE(currentReleaseId), 'Scenario E (Test Failure)')}
              className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {loadingScenario === 'E' ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Run
            </button>
          </div>
        </div>

        <div className="mt-5 pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
