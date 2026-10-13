export type DecisionType = 
  | 'APPROVE'
  | 'REVIEW'
  | 'BLOCK'
  | 'PENDING_ASSESSMENT'
  | 'INSUFFICIENT_EVIDENCE';

export interface ProjectPolicy {
  approval_threshold: number;
  review_threshold: number;
  require_provenance: boolean;
  require_sbom: boolean;
  require_tests: boolean;
  require_dependency_scan: boolean;
  block_on_critical_vuln: boolean;
  block_on_high_vuln_count: number;
  block_on_hash_mismatch: boolean;
  require_cosign_verification: boolean;
  policy_version: string;
}

export interface Project {
  project_id: string;
  name: string;
  description: string;
  repository_url?: string;
  policy: ProjectPolicy;
  created_at: string;
  updated_at: string;
  created_by: string;
  releases_count: number;
}

export interface ArtifactDescriptor {
  filename: string;
  s3_key?: string;
  expected_sha256: string;
  size_bytes?: number;
  download_url?: string;
}

export interface Release {
  release_id: string;
  project_id: string;
  version: string;
  source_commit: string;
  artifact: ArtifactDescriptor;
  evidence_requirements: {
    sbom_required: boolean;
    provenance_required: boolean;
    tests_required: boolean;
    dependency_scan_required: boolean;
  };
  policy_version: string;
  environment: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  latest_assessment_id?: string;
  latest_decision: DecisionType;
  latest_trust_score?: number;
  evidence_counts: Record<string, number>;
}

export interface ScoreComponentDetail {
  name: string;
  weight: number;
  score?: number;
  status: 'VERIFIED' | 'FAILED' | 'MISSING' | 'PARTIAL' | 'NOT_REQUIRED';
  details: string;
}

export interface TrustScoreBreakdown {
  integrity_score?: number;
  dependency_score?: number;
  provenance_score?: number;
  test_score?: number;
  completeness_score: number;
  formula: string;
  components: ScoreComponentDetail[];
}

export interface AIAnomalyResult {
  anomaly_detected: boolean;
  anomaly_score: number;
  model_version: string;
  model_available: boolean;
  feature_importance_summary?: string;
  confidence_note: string;
}

export interface ExplanationItem {
  rule_or_factor: string;
  impact: 'BLOCK' | 'PENALTY' | 'NEUTRAL' | 'POSITIVE';
  message: string;
  evidence_ref?: string;
}

export interface AssessmentRecord {
  assessment_id: string;
  project_id: string;
  release_id: string;
  assessment_version: number;
  trust_score?: number;
  decision: DecisionType;
  policy_version: string;
  score_breakdown: TrustScoreBreakdown;
  blocking_reasons: string[];
  risk_factors: string[];
  recommendations: string[];
  explanations: ExplanationItem[];
  ai_anomaly?: AIAnomalyResult;
  evidence_ids_used: string[];
  previous_assessment_id?: string;
  created_at: string;
  engine_version: string;
}

export interface EvidenceEnvelope {
  evidence_id: string;
  project_id: string;
  release_id: string;
  evidence_type: string;
  schema_version: string;
  evidence_version: number;
  source: string;
  observed_at: string;
  received_at: string;
  validation_status: string;
  payload: Record<string, any>;
  content_sha256: string;
  correlation_id: string;
}

export interface AuditEvent {
  event_id: string;
  event_type: string;
  project_id: string;
  release_id: string;
  previous_assessment_version?: number;
  new_assessment_version?: number;
  previous_decision?: string;
  new_decision?: string;
  reason_codes: string[];
  timestamp: string;
  actor: string;
  details: Record<string, any>;
}

export interface DashboardMetrics {
  total_projects: number;
  total_releases: number;
  approved_releases: number;
  review_releases: number;
  blocked_releases: number;
  insufficient_evidence_releases: number;
  pending_releases: number;
  average_trust_score: number;
}

export interface DashboardSummary {
  metrics: DashboardMetrics;
  vulnerability_distribution: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  recent_events: AuditEvent[];
  recent_releases: Release[];
}
