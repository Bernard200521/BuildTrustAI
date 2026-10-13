import axios from 'axios';
import {
  DashboardSummary,
  Project,
  Release,
  AssessmentRecord,
  EvidenceEnvelope,
  AuditEvent,
  ProjectPolicy
} from '../types';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Demo admin auto-auth helper
let authToken: string | null = null;

export async function ensureAuthenticated(): Promise<string> {
  if (authToken) return authToken;
  try {
    const res = await axios.post(`${API_BASE}/auth/login`, {
      email: 'admin@buildtrust.ai',
      password: 'BuildTrustAdmin2026!'
    });
    authToken = res.data.access_token;
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
    return authToken as string;
  } catch (err) {
    console.warn('Auto-auth failed, continuing unauthenticated', err);
    return '';
  }
}

// Attach interceptor
apiClient.interceptors.request.use(async (config) => {
  if (!authToken) {
    await ensureAuthenticated();
  }
  if (authToken && !config.headers['Authorization']) {
    config.headers['Authorization'] = `Bearer ${authToken}`;
  }
  return config;
});

export const api = {
  async getDashboardSummary(): Promise<DashboardSummary> {
    const res = await apiClient.get<DashboardSummary>('/dashboard/summary');
    return res.data;
  },

  async getProjects(): Promise<Project[]> {
    const res = await apiClient.get<{ items: Project[]; total: number }>('/projects');
    return res.data.items;
  },

  async getReleases(projectId?: string): Promise<Release[]> {
    const res = await apiClient.get<{ items: Release[]; total: number }>('/releases', {
      params: projectId ? { project_id: projectId } : {}
    });
    return res.data.items;
  },

  async getRelease(releaseId: string): Promise<Release> {
    const res = await apiClient.get<Release>(`/releases/${releaseId}`);
    return res.data;
  },

  async getLatestAssessment(releaseId: string): Promise<AssessmentRecord> {
    const res = await apiClient.get<AssessmentRecord>(`/releases/${releaseId}/assessments/latest`);
    return res.data;
  },

  async getAssessmentHistory(releaseId: string): Promise<AssessmentRecord[]> {
    const res = await apiClient.get<{ items: AssessmentRecord[]; total: number }>(`/releases/${releaseId}/assessments/history`);
    return res.data.items;
  },

  async getReleaseEvidence(releaseId: string): Promise<EvidenceEnvelope[]> {
    const res = await apiClient.get<{ items: EvidenceEnvelope[]; total: number }>(`/releases/${releaseId}/evidence`);
    return res.data.items;
  },

  async getAuditEvents(releaseId?: string): Promise<AuditEvent[]> {
    if (releaseId) {
      const res = await apiClient.get<{ items: AuditEvent[]; total: number }>(`/releases/${releaseId}/audit`);
      return res.data.items;
    }
    const summary = await api.getDashboardSummary();
    return summary.recent_events;
  },

  async triggerReassessment(releaseId: string): Promise<AssessmentRecord> {
    const res = await apiClient.post<AssessmentRecord>(`/releases/${releaseId}/assessments`);
    return res.data;
  },

  async submitEvidence(releaseId: string, submission: any): Promise<any> {
    const res = await apiClient.post(`/releases/${releaseId}/evidence`, submission);
    return res.data;
  },

  async updateProjectPolicy(projectId: string, policy: ProjectPolicy): Promise<Project> {
    const res = await apiClient.put<Project>(`/projects/${projectId}/policy`, policy);
    return res.data;
  },

  // Simulator controls
  async getSimulatorStatus(): Promise<{ is_running: boolean; tick_count: number; interval_seconds: number }> {
    const res = await apiClient.get('/simulator/status');
    return res.data;
  },

  async startSimulator(intervalSeconds: number = 6.0): Promise<any> {
    const res = await apiClient.post(`/simulator/start?interval_seconds=${intervalSeconds}`);
    return res.data;
  },

  async stopSimulator(): Promise<any> {
    const res = await apiClient.post('/simulator/stop');
    return res.data;
  },

  async triggerSimulatorTick(): Promise<any> {
    const res = await apiClient.post('/simulator/tick');
    return res.data;
  },

  // Real backend scenario triggers
  async triggerScenarioA(releaseId: string = 'rel-payment-1.0.0'): Promise<any> {
    const res = await apiClient.post(`/simulator/scenarios/a?release_id=${encodeURIComponent(releaseId)}`);
    return res.data;
  },

  async triggerScenarioB(releaseId: string = 'rel-payment-1.0.0'): Promise<any> {
    const res = await apiClient.post(`/simulator/scenarios/b?release_id=${encodeURIComponent(releaseId)}`);
    return res.data;
  },

  async triggerScenarioC(releaseId: string = 'rel-payment-1.0.0'): Promise<any> {
    const res = await apiClient.post(`/simulator/scenarios/c?release_id=${encodeURIComponent(releaseId)}`);
    return res.data;
  },

  async triggerScenarioD(releaseId: string = 'rel-payment-1.0.0'): Promise<any> {
    const res = await apiClient.post(`/simulator/scenarios/d?release_id=${encodeURIComponent(releaseId)}`);
    return res.data;
  },

  async triggerScenarioE(releaseId: string = 'rel-payment-1.0.0'): Promise<any> {
    const res = await apiClient.post(`/simulator/scenarios/e?release_id=${encodeURIComponent(releaseId)}`);
    return res.data;
  }
};
