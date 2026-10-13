import React, { useState } from 'react';
import { api } from '../api/client';
import { Project, ProjectPolicy } from '../types';
import { ShieldCheck, Sliders, Save, CheckCircle2, Lock } from 'lucide-react';

interface Props {
  projects: Project[];
  onProjectUpdated: () => void;
}

export const SecuritySettingsPage: React.FC<Props> = ({ projects, onProjectUpdated }) => {
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projects[0]?.project_id || '');
  const [saving, setSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const currentProject = projects.find((p) => p.project_id === selectedProjectId) || projects[0];
  const [policy, setPolicy] = useState<ProjectPolicy>(currentProject?.policy || {
    approval_threshold: 85.0,
    review_threshold: 60.0,
    require_provenance: true,
    require_sbom: true,
    require_tests: true,
    require_dependency_scan: true,
    block_on_critical_vuln: true,
    block_on_high_vuln_count: 3,
    block_on_hash_mismatch: true,
    require_cosign_verification: false,
    policy_version: '1.0'
  });

  const handleSave = async () => {
    if (!currentProject) return;
    setSaving(true);
    setSaveSuccess(null);
    try {
      await api.updateProjectPolicy(currentProject.project_id, policy);
      setSaveSuccess(`Policy for ${currentProject.project_id} updated successfully!`);
      onProjectUpdated();
    } catch (err: any) {
      alert(`Failed to save policy: ${err?.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white">Security Policy Engine Configuration</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              POLICY v{policy.policy_version}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Configure deterministic release thresholds, mandatory blocking criteria, and verification requirements.
          </p>
        </div>

        {/* Project Selector */}
        {projects.length > 0 && (
          <select
            value={selectedProjectId}
            onChange={(e) => {
              setSelectedProjectId(e.target.value);
              const p = projects.find((x) => x.project_id === e.target.value);
              if (p) setPolicy(p.policy);
            }}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none cursor-pointer"
          >
            {projects.map((p) => (
              <option key={p.project_id} value={p.project_id}>
                {p.name} ({p.project_id})
              </option>
            ))}
          </select>
        )}
      </div>

      {saveSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{saveSuccess}</span>
        </div>
      )}

      {/* Main Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scoring Thresholds */}
        <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-white mb-2">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <span>Trust Score Release Gate Thresholds</span>
          </div>

          <div>
            <label className="text-xs text-slate-300 font-medium block mb-1">
              Approval Threshold (≥ Score eligible for APPROVE)
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="50"
                max="100"
                step="1"
                value={policy.approval_threshold}
                onChange={(e) => setPolicy({ ...policy, approval_threshold: parseFloat(e.target.value) })}
                className="flex-1 accent-emerald-500 cursor-pointer"
              />
              <span className="font-mono text-sm font-bold text-emerald-400 w-12 text-right">
                {policy.approval_threshold}
              </span>
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-300 font-medium block mb-1">
              Review Threshold (Score below triggers BLOCK; between Review & Approval triggers REVIEW)
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="0"
                max="80"
                step="1"
                value={policy.review_threshold}
                onChange={(e) => setPolicy({ ...policy, review_threshold: parseFloat(e.target.value) })}
                className="flex-1 accent-amber-500 cursor-pointer"
              />
              <span className="font-mono text-sm font-bold text-amber-400 w-12 text-right">
                {policy.review_threshold}
              </span>
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-300 font-medium block mb-1">
              High-Severity Vulnerability Tolerance Limit
            </label>
            <input
              type="number"
              min="0"
              max="20"
              value={policy.block_on_high_vuln_count}
              onChange={(e) => setPolicy({ ...policy, block_on_high_vuln_count: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200"
            />
          </div>
        </div>

        {/* Mandatory Security Gate Rules */}
        <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3.5">
          <div className="flex items-center gap-2 text-sm font-semibold text-white mb-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            <span>Mandatory Deterministic Security Gates</span>
          </div>

          <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
            <div>
              <div className="text-xs font-semibold text-slate-200">Zero-Tolerance Critical Vulnerabilities</div>
              <div className="text-[11px] text-slate-400">Instantly block any release candidate with ≥ 1 critical CVE</div>
            </div>
            <input
              type="checkbox"
              checked={policy.block_on_critical_vuln}
              onChange={(e) => setPolicy({ ...policy, block_on_critical_vuln: e.target.checked })}
              className="accent-emerald-500 h-4 w-4"
            />
          </label>

          <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
            <div>
              <div className="text-xs font-semibold text-slate-200">Enforce Cryptographic Hash Match</div>
              <div className="text-[11px] text-slate-400">Block candidate if calculated artifact digest differs from manifest</div>
            </div>
            <input
              type="checkbox"
              checked={policy.block_on_hash_mismatch}
              onChange={(e) => setPolicy({ ...policy, block_on_hash_mismatch: e.target.checked })}
              className="accent-emerald-500 h-4 w-4"
            />
          </label>

          <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
            <div>
              <div className="text-xs font-semibold text-slate-200">Require SLSA Build Provenance</div>
              <div className="text-[11px] text-slate-400">Require verified builder identity and git commit matching</div>
            </div>
            <input
              type="checkbox"
              checked={policy.require_provenance}
              onChange={(e) => setPolicy({ ...policy, require_provenance: e.target.checked })}
              className="accent-emerald-500 h-4 w-4"
            />
          </label>

          <label className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
            <div>
              <div className="text-xs font-semibold text-slate-200">Require Cosign Cryptographic Signature</div>
              <div className="text-[11px] text-slate-400">Enforce Cosign signature verification on provenance attestations</div>
            </div>
            <input
              type="checkbox"
              checked={policy.require_cosign_verification}
              onChange={(e) => setPolicy({ ...policy, require_cosign_verification: e.target.checked })}
              className="accent-emerald-500 h-4 w-4"
            />
          </label>
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-950/40 transition-colors cursor-pointer"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Updating Policy...' : 'Save Policy Configuration'}</span>
        </button>
      </div>
    </div>
  );
};
