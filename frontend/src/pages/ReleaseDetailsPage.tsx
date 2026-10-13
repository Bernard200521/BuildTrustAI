import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Release, AssessmentRecord, EvidenceEnvelope } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ScoreGauge } from '../components/ScoreGauge';
import { 
  ShieldCheck, 
  AlertTriangle, 
  XCircle, 
  FileCode, 
  GitBranch, 
  Box, 
  CheckCircle2, 
  RefreshCw,
  ExternalLink,
  Lock,
  Layers,
  Sparkles
} from 'lucide-react';

interface Props {
  releaseId: string;
  releases: Release[];
  onSelectRelease: (id: string) => void;
  onOpenDemoModal: () => void;
}

export const ReleaseDetailsPage: React.FC<Props> = ({ 
  releaseId, 
  releases, 
  onSelectRelease, 
  onOpenDemoModal 
}) => {
  const [assessment, setAssessment] = useState<AssessmentRecord | null>(null);
  const [evidenceList, setEvidenceList] = useState<EvidenceEnvelope[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeEvidenceTab, setActiveEvidenceTab] = useState<'integrity' | 'sbom' | 'vulns' | 'provenance' | 'tests'>('integrity');
  const [reassessing, setReassessing] = useState<boolean>(false);

  const currentRelease = releases.find((r) => r.release_id === releaseId) || releases[0];

  const loadData = async (rid: string) => {
    setLoading(true);
    try {
      const [asm, evs] = await Promise.all([
        api.getLatestAssessment(rid).catch(() => null),
        api.getReleaseEvidence(rid).catch(() => [])
      ]);
      setAssessment(asm);
      setEvidenceList(evs);
    } catch (err) {
      console.error('Failed to load release details', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (releaseId) {
      loadData(releaseId);
    }
  }, [releaseId]);

  const handleManualReassess = async () => {
    if (!currentRelease) return;
    setReassessing(true);
    try {
      const asm = await api.triggerReassessment(currentRelease.release_id);
      setAssessment(asm);
      const evs = await api.getReleaseEvidence(currentRelease.release_id);
      setEvidenceList(evs);
    } catch (err) {
      console.error('Manual reassessment failed', err);
    } finally {
      setReassessing(false);
    }
  };

  if (!currentRelease) {
    return <div className="text-slate-400 p-8">No release candidates found.</div>;
  }

  // Filter evidence envelopes by type - pick latest received envelope
  const getLatestEvidence = (type: string) => {
    const matches = evidenceList.filter((e) => e.evidence_type === type);
    return matches.length > 0 ? matches[matches.length - 1] : undefined;
  };
  const integrityEv = getLatestEvidence('artifact_integrity');
  const sbomEv = getLatestEvidence('sbom');
  const vulnEv = getLatestEvidence('vulnerability_scan');
  const provEv = getLatestEvidence('provenance');
  const testEv = getLatestEvidence('test_results');

  return (
    <div className="space-y-6">
      {/* Header Selector & Action Bar */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold font-mono text-white">{currentRelease.release_id}</h2>
            <StatusBadge decision={assessment?.decision ?? currentRelease.latest_decision} size="md" />
            {assessment && (
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700" title={`Assessment ID: ${assessment.assessment_id}`}>
                  Version #{assessment.assessment_version}
                </span>
                <span className="text-[11px] font-mono text-slate-500">
                  {new Date(assessment.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
            <span>Project: <strong className="text-slate-200">{currentRelease.project_id}</strong></span>
            <span>•</span>
            <span>Version: <strong className="text-slate-200">{currentRelease.version}</strong></span>
            <span>•</span>
            <span>Env: <strong className="text-slate-200 uppercase">{currentRelease.environment}</strong></span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Release Switcher */}
          <select
            value={currentRelease.release_id}
            onChange={(e) => onSelectRelease(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none cursor-pointer"
          >
            {releases.map((r) => (
              <option key={r.release_id} value={r.release_id}>
                {r.release_id} ({r.project_id} - v{r.version})
              </option>
            ))}
          </select>

          <button
            onClick={handleManualReassess}
            disabled={reassessing}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reassessing ? 'animate-spin' : ''}`} />
            <span>Reassess</span>
          </button>

          <button
            onClick={onOpenDemoModal}
            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Simulate Evidence Changes</span>
          </button>
        </div>
      </div>

      {/* Main Score & Gate Banner */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trust Score Gauge Card */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Release Trust Index</span>
              <span className="text-[10px] font-mono text-emerald-400">ECTE FORMULA T</span>
            </div>
            <ScoreGauge score={assessment?.trust_score ?? currentRelease.latest_trust_score} size="lg" />
          </div>
          <div className="mt-4 pt-4 border-t border-slate-800 text-center">
            <span className="text-[11px] font-mono text-slate-400">
              T = 0.25*I + 0.20*D + 0.20*P + 0.15*S + 0.20*E
            </span>
          </div>
        </div>

        {/* Blocking Reasons & Status */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Policy Gate Evaluation</span>
              <StatusBadge decision={currentRelease.latest_decision} size="sm" />
            </div>

            {assessment?.blocking_reasons && assessment.blocking_reasons.length > 0 ? (
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 mb-4">
                <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs mb-2">
                  <XCircle className="w-4 h-4" />
                  <span>Mandatory Security Gate Blocking Conditions:</span>
                </div>
                <ul className="space-y-1 pl-6 list-disc text-xs text-rose-300">
                  {assessment.blocking_reasons.map((reason, idx) => (
                    <li key={idx}>{reason}</li>
                  ))}
                </ul>
              </div>
            ) : currentRelease.latest_decision === 'APPROVE' ? (
              <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 mb-4 text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <span>All mandatory security gates passed. Release candidate meets organizational trust thresholds.</span>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/30 mb-4 text-xs text-amber-300 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                <span>Release candidate requires human SecOps review before promotion.</span>
              </div>
            )}

            {/* Recommendations */}
            {assessment?.recommendations && assessment.recommendations.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-slate-300 mb-1.5 block">Actionable Recommendations:</span>
                <ul className="space-y-1 text-xs text-slate-400 pl-4 list-disc">
                  {assessment.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
            <span>Commit: <strong className="font-mono text-slate-400">{currentRelease.source_commit}</strong></span>
            <span>Policy Version: <strong className="font-mono text-slate-400">{assessment?.policy_version || '1.0'}</strong></span>
          </div>
        </div>
      </div>

      {/* Component Breakdown Cards (I, D, P, S, E) */}
      {assessment?.score_breakdown && (
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Component Breakdown (ECTE Weights)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {assessment.score_breakdown.components.map((comp, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-semibold text-slate-200">{comp.name}</span>
                  <span className={`text-[10px] font-bold font-mono px-1.5 py-0.2 rounded ${
                    comp.status === 'VERIFIED' ? 'bg-emerald-950 text-emerald-400' :
                    comp.status === 'FAILED' ? 'bg-rose-950 text-rose-400' :
                    comp.status === 'PARTIAL' ? 'bg-amber-950 text-amber-400' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {comp.status}
                  </span>
                </div>
                <div className="text-lg font-bold font-mono text-white mb-1">
                  {comp.score !== null && comp.score !== undefined ? `${comp.score.toFixed(1)}` : 'N/A'}
                  <span className="text-[10px] text-slate-500 font-normal"> (w={comp.weight})</span>
                </div>
                <p className="text-[10px] text-slate-400 leading-tight line-clamp-2" title={comp.details}>
                  {comp.details}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Envelopes Deep Dive */}
      <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Verified Release Evidence Streams</h3>
            <p className="text-xs text-slate-400">Inspect raw cryptographic integrity, SBOM, vulnerabilities, provenance, and tests</p>
          </div>
          
          {/* Sub Tabs */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveEvidenceTab('integrity')}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                activeEvidenceTab === 'integrity' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Artifact SHA-256
            </button>
            <button
              onClick={() => setActiveEvidenceTab('sbom')}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                activeEvidenceTab === 'sbom' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              CycloneDX SBOM
            </button>
            <button
              onClick={() => setActiveEvidenceTab('vulns')}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                activeEvidenceTab === 'vulns' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              OSV Vulnerabilities
            </button>
            <button
              onClick={() => setActiveEvidenceTab('provenance')}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                activeEvidenceTab === 'provenance' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              SLSA Provenance
            </button>
            <button
              onClick={() => setActiveEvidenceTab('tests')}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                activeEvidenceTab === 'tests' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Test Results
            </button>
          </div>
        </div>

        {/* Tab 1: Artifact Integrity */}
        {activeEvidenceTab === 'integrity' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs">
                <span className="text-[10px] text-slate-500 uppercase block mb-1">Expected SHA-256 (Release Manifest)</span>
                <span className="text-slate-200 break-all select-all">{currentRelease.artifact.expected_sha256}</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs">
                <span className="text-[10px] text-slate-500 uppercase block mb-1">Calculated SHA-256 (Artifact Verifier)</span>
                <span className={`break-all select-all ${
                  integrityEv?.payload?.matches ? 'text-emerald-400' : 'text-rose-400'
                }`}>
                  {integrityEv?.payload?.calculated_sha256 || 'No artifact binary uploaded yet'}
                </span>
              </div>
            </div>
            {integrityEv && (
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                <span className="text-slate-400">Verification Outcome: <strong className={integrityEv.payload.matches ? 'text-emerald-400' : 'text-rose-400'}>{integrityEv.payload.matches ? 'MATCH (Verified Integrity)' : 'MISMATCH (Tampering Detected)'}</strong></span>
                <span className="text-slate-500 font-mono text-[11px]">Size: {integrityEv.payload.byte_size || 0} bytes</span>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: CycloneDX SBOM */}
        {activeEvidenceTab === 'sbom' && (
          <div>
            {sbomEv ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                  <span>Format: <strong className="text-slate-200">{sbomEv.payload.format} v{sbomEv.payload.spec_version}</strong></span>
                  <span>Component Count: <strong className="text-emerald-400">{sbomEv.payload.component_count}</strong></span>
                </div>
                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3">Component Name</th>
                        <th className="py-2.5 px-3">Version</th>
                        <th className="py-2.5 px-3">Type</th>
                        <th className="py-2.5 px-3">Package URL (PURL)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                      {sbomEv.payload.components?.map((c: any, i: number) => (
                        <tr key={i} className="hover:bg-slate-800/30">
                          <td className="py-2 px-3 text-slate-200 font-semibold">{c.name}</td>
                          <td className="py-2 px-3 text-slate-400">{c.version}</td>
                          <td className="py-2 px-3 text-slate-500 uppercase">{c.type || 'library'}</td>
                          <td className="py-2 px-3 text-slate-500 text-[10px] truncate max-w-xs">{c.purl || '--'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center">No SBOM evidence submitted.</div>
            )}
          </div>
        )}

        {/* Tab 3: Vulnerabilities */}
        {activeEvidenceTab === 'vulns' && (
          <div>
            {vulnEv ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                  <span>Scanner: <strong className="text-slate-200">{vulnEv.payload.scanner_name}</strong></span>
                  <span>Findings: <strong className="text-rose-400">{vulnEv.payload.total_findings} vulnerabilities</strong></span>
                </div>
                {vulnEv.payload.findings?.length > 0 ? (
                  <div className="overflow-x-auto rounded-xl border border-slate-800">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                        <tr>
                          <th className="py-2.5 px-3">Advisory ID</th>
                          <th className="py-2.5 px-3">Package</th>
                          <th className="py-2.5 px-3">Version</th>
                          <th className="py-2.5 px-3">Severity</th>
                          <th className="py-2.5 px-3">CVSS</th>
                          <th className="py-2.5 px-3">Fixed Version</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                        {vulnEv.payload.findings.map((f: any, i: number) => (
                          <tr key={i} className="hover:bg-slate-800/30">
                            <td className="py-2 px-3 text-rose-400 font-semibold">{f.id}</td>
                            <td className="py-2 px-3 text-slate-200">{f.package}</td>
                            <td className="py-2 px-3 text-slate-400">{f.version}</td>
                            <td className="py-2 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                f.severity === 'CRITICAL' ? 'bg-rose-950 text-rose-400 border border-rose-500/30' :
                                f.severity === 'HIGH' ? 'bg-orange-950 text-orange-400 border border-orange-500/30' :
                                'bg-amber-950 text-amber-400 border border-amber-500/30'
                              }`}>
                                {f.severity}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-slate-300">{f.cvss_score || '--'}</td>
                            <td className="py-2 px-3 text-emerald-400">{f.fixed_version || 'None'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-xs text-emerald-400">
                    No known CVE vulnerabilities detected by scanner.
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center">No vulnerability scan evidence submitted.</div>
            )}
          </div>
        )}

        {/* Tab 4: Provenance */}
        {activeEvidenceTab === 'provenance' && (
          <div>
            {provEv ? (
              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block mb-1">Builder Identity</span>
                    <span className="text-slate-200">{provEv.payload.builder_id}</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block mb-1">SLSA Build Level</span>
                    <span className="text-emerald-400 font-bold">{provEv.payload.slsa_level}</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block mb-1">Source Revision</span>
                    <span className="text-slate-300">{provEv.payload.source_revision}</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block mb-1">Cosign Attestation Status</span>
                    <span className={`font-bold ${
                      provEv.payload.cosign_verified === 'VERIFIED' ? 'text-emerald-400' :
                      provEv.payload.cosign_verified === 'FAILED' ? 'text-rose-400' : 'text-slate-400'
                    }`}>
                      {provEv.payload.cosign_verified}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center">No provenance evidence submitted.</div>
            )}
          </div>
        )}

        {/* Tab 5: Tests */}
        {activeEvidenceTab === 'tests' && (
          <div>
            {testEv ? (
              <div className="space-y-3 text-xs">
                <div className="flex items-center gap-4 p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span>Total: <strong className="font-mono text-white">{testEv.payload.total_tests}</strong></span>
                  <span>Passed: <strong className="font-mono text-emerald-400">{testEv.payload.passed}</strong></span>
                  <span>Failed: <strong className="font-mono text-rose-400">{testEv.payload.failed}</strong></span>
                  <span>Mandatory Passed: <strong className={testEv.payload.mandatory_tests_passed ? 'text-emerald-400' : 'text-rose-400'}>
                    {testEv.payload.mandatory_tests_passed ? 'YES' : 'NO'}
                  </strong></span>
                </div>
                {testEv.payload.suites && (
                  <div className="space-y-2">
                    {testEv.payload.suites.map((s: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] font-mono">
                        <span className="text-slate-200">{s.name}</span>
                        <span className={s.passed ? 'text-emerald-400' : 'text-rose-400'}>
                          {s.passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center">No test results submitted.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
