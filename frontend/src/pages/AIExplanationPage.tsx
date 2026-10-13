import React from 'react';
import { Release, AssessmentRecord } from '../types';
import { 
  BrainCircuit, 
  ShieldCheck, 
  AlertTriangle, 
  Info, 
  Sliders, 
  HelpCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface Props {
  releases: Release[];
  selectedReleaseId: string;
  onSelectRelease: (id: string) => void;
  assessment: AssessmentRecord | null;
}

export const AIExplanationPage: React.FC<Props> = ({ 
  releases, 
  selectedReleaseId, 
  onSelectRelease,
  assessment 
}) => {
  const currentRelease = releases.find((r) => r.release_id === selectedReleaseId) || releases[0];

  const aiAnomaly = assessment?.ai_anomaly;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white">AI-Assisted Risk Prioritization & Explanations</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30">
              EXPLAINABLE AI ENGINE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Transparent evidence-grounded risk rationales and scikit-learn IsolationForest anomaly signals.
          </p>
        </div>

        {/* Release Switcher */}
        <select
          value={currentRelease?.release_id}
          onChange={(e) => onSelectRelease(e.target.value)}
          className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none cursor-pointer"
        >
          {releases.map((r) => (
            <option key={r.release_id} value={r.release_id}>
              {r.release_id} ({r.project_id})
            </option>
          ))}
        </select>
      </div>

      {/* Triad Distinction Banner (Observed Facts vs Model Output vs Policy Decisions) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/40 border border-sky-500/20">
          <div className="flex items-center gap-2 text-sky-400 text-xs font-bold mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>1. Observed Facts (Verified Evidence)</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Cryptographic SHA-256 digests, CycloneDX SBOM components, verified OSV CVE advisories, and SLSA builder attestations.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/40 border border-purple-500/20">
          <div className="flex items-center gap-2 text-purple-400 text-xs font-bold mb-1">
            <BrainCircuit className="w-4 h-4" />
            <span>2. Model Output (ML IsolationForest)</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Multi-dimensional feature vector anomaly score for SecOps triage. Serves as a review signal—never overrides policy.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/40 border border-emerald-500/20">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold mb-1">
            <Sliders className="w-4 h-4" />
            <span>3. Policy Decisions (Deterministic Gate)</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Strict, deterministic gate rules (hash mismatch = BLOCK, critical CVE = BLOCK, approval threshold = 85.0). Absolute final authority.
          </p>
        </div>
      </div>

      {/* ML Model Card & Anomaly Signal */}
      <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">IsolationForest Anomaly Prioritization</h3>
            <p className="text-xs text-slate-400">Trained on reproducible multi-dimensional release verification profiles</p>
          </div>
          <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300">
            {aiAnomaly?.model_version || 'IsolationForest-v1.0'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
            <div className="text-[11px] text-slate-500 uppercase tracking-wider mb-1">Anomaly Indicator</div>
            <div className={`text-xl font-bold font-mono ${
              aiAnomaly?.anomaly_detected ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {aiAnomaly?.anomaly_detected ? 'FLAGGED ANOMALOUS' : 'NOMINAL PROFILE'}
            </div>
            <div className="text-[10px] text-slate-500 mt-1 font-mono">
              Score: {aiAnomaly?.anomaly_score?.toFixed(3) ?? '0.000'}
            </div>
          </div>

          <div className="md:col-span-2 space-y-2 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-400 block font-semibold mb-1">Feature Contribution Analysis:</span>
              <p className="text-slate-300 leading-relaxed font-mono text-[11px]">
                {aiAnomaly?.feature_importance_summary || 'Feature metrics align with expected release baseline distribution.'}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 flex items-start gap-2">
              <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
              <span>{aiAnomaly?.confidence_note || 'IsolationForest provides an anomaly prioritization signal; release gates are enforced deterministically.'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Deterministic Explanations Feed */}
      <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800">
        <h3 className="text-sm font-semibold text-white mb-1">Evidence-Grounded Policy Explanations</h3>
        <p className="text-xs text-slate-400 mb-4">Every factor evaluated by the Evidence-Change Trust Engine (ECTE)</p>

        {assessment?.explanations && assessment.explanations.length > 0 ? (
          <div className="space-y-2.5">
            {assessment.explanations.map((exp, idx) => (
              <div 
                key={idx} 
                className={`p-3.5 rounded-xl border text-xs flex items-start gap-3 ${
                  exp.impact === 'BLOCK' ? 'bg-rose-950/20 border-rose-500/30 text-rose-300' :
                  exp.impact === 'PENALTY' ? 'bg-amber-950/20 border-amber-500/30 text-amber-300' :
                  exp.impact === 'POSITIVE' ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300' :
                  'bg-slate-950 border-slate-800 text-slate-300'
                }`}
              >
                {exp.impact === 'BLOCK' && <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />}
                {exp.impact === 'PENALTY' && <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />}
                {exp.impact === 'POSITIVE' && <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />}
                <div>
                  <div className="font-mono text-[11px] font-bold tracking-wider mb-0.5">{exp.rule_or_factor}</div>
                  <div className="leading-relaxed">{exp.message}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-slate-500 py-6 text-center">No explanation items generated yet.</div>
        )}
      </div>
    </div>
  );
};
