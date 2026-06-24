'use client';

import { getToken, clearToken } from './auth';
import type {
  Alert,
  AuthResponse,
  User,
  Customer,
  AIPolicy,
  Allowlist,
  Investigation,
  Feedback,
  Report,
  AIProvider,
  ProviderHealth,
  AIRun,
  UsageSummary,
  Playbook,
  DashboardSummary,
  DailySummary,
  MitreSummary,
  AIOperationsSummary,
  AuditLog,
} from './types';

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  body?: any;
  constructor(message: string, status: number, body?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: any;
  /** Send/return raw text instead of JSON */
  raw?: boolean;
}

export async function apiFetch<T = any>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, raw, headers, ...rest } = options;
  const token = getToken();

  const finalHeaders: Record<string, string> = {
    Accept: raw ? 'text/markdown, text/plain, */*' : 'application/json',
    ...(headers as Record<string, string>),
  };
  if (token) finalHeaders['Authorization'] = `Bearer ${token}`;

  let finalBody: BodyInit | undefined;
  if (body !== undefined) {
    if (typeof body === 'string' || body instanceof FormData) {
      finalBody = body as BodyInit;
    } else {
      finalHeaders['Content-Type'] = 'application/json';
      finalBody = JSON.stringify(body);
    }
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...rest,
      headers: finalHeaders,
      body: finalBody,
      cache: 'no-store',
    });
  } catch (e: any) {
    throw new ApiError(
      `Network error: cannot reach API at ${API_BASE}. Is the backend running?`,
      0,
      e?.message
    );
  }

  if (res.status === 401) {
    clearToken();
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
    throw new ApiError('Unauthorized', 401);
  }

  if (!res.ok) {
    let errBody: any;
    try {
      errBody = await res.json();
    } catch {
      try {
        errBody = await res.text();
      } catch {
        errBody = undefined;
      }
    }
    const msg =
      (errBody && (errBody.detail || errBody.message)) ||
      `Request failed (${res.status})`;
    throw new ApiError(
      typeof msg === 'string' ? msg : JSON.stringify(msg),
      res.status,
      errBody
    );
  }

  if (raw) {
    return (await res.text()) as unknown as T;
  }

  if (res.status === 204) return undefined as unknown as T;

  const text = await res.text();
  if (!text) return undefined as unknown as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}

/** Normalize list-ish responses: backend may return [] or {items: []} */
function asList<T>(data: any): T[] {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  if (data && Array.isArray(data.results)) return data.results;
  if (data && Array.isArray(data.data)) return data.data;
  return [];
}

// ---------------------------------------------------------------------------
// Typed API surface
// ---------------------------------------------------------------------------

export const api = {
  // Auth
  login: (email: string, password: string) =>
    apiFetch<AuthResponse>('/auth/login', {
      method: 'POST',
      body: { email, password },
    }),
  register: (email: string, password: string, name?: string, organization_name?: string) =>
    apiFetch<AuthResponse>('/auth/register', {
      method: 'POST',
      body: { email, password, full_name: name, organization_name },
    }),
  me: () => apiFetch<User>('/auth/me'),
  logout: () => apiFetch<any>('/auth/logout', { method: 'POST' }),

  // Response recommendations & approval workflow
  listRecommendations: (investigationId: string | number) =>
    apiFetch<any[]>(`/investigations/${investigationId}/recommendations`),
  requestApproval: (recommendationId: number) =>
    apiFetch<any>(`/recommendations/${recommendationId}/request-approval`, { method: 'POST' }),
  listApprovals: () => apiFetch<any[]>('/approvals'),
  decideApproval: (approvalId: number, decision: 'approved' | 'rejected', note?: string) =>
    apiFetch<any>(`/approvals/${approvalId}/decision`, { method: 'POST', body: { decision, note } }),

  // Knowledge documents (SOPs)
  listKnowledge: (customerId?: string) =>
    apiFetch<any[]>(`/knowledge${customerId ? `?customer_id=${customerId}` : ''}`),
  createKnowledge: (body: { title: string; content: string; doc_type?: string; customer_id?: number }) =>
    apiFetch<any>('/knowledge', { method: 'POST', body }),

  // Customers
  listCustomers: () =>
    apiFetch<any>('/customers').then((d) => asList<Customer>(d)),
  getCustomer: (id: string) => apiFetch<Customer>(`/customers/${id}`),
  createCustomer: (body: Partial<Customer>) =>
    apiFetch<Customer>('/customers', { method: 'POST', body }),
  updateCustomer: (id: string, body: Partial<Customer>) =>
    apiFetch<Customer>(`/customers/${id}`, { method: 'PUT', body }),
  getAiPolicy: (id: string) =>
    apiFetch<AIPolicy>(`/customers/${id}/ai-policy`),
  updateAiPolicy: (id: string, body: Partial<AIPolicy>) =>
    apiFetch<AIPolicy>(`/customers/${id}/ai-policy`, { method: 'PUT', body }),

  // Alerts
  listAlerts: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiFetch<any>(`/alerts${qs}`).then((d) => asList<Alert>(d));
  },
  getAlert: (id: string) => apiFetch<Alert>(`/alerts/${id}`),
  submitAlert: (body: any) =>
    apiFetch<Alert>('/alerts', { method: 'POST', body }),
  parseAlert: (id: string) =>
    apiFetch<Alert>(`/alerts/${id}/parse`, { method: 'POST' }),
  enrichAlert: (id: string) =>
    apiFetch<Alert>(`/alerts/${id}/enrich`, { method: 'POST' }),
  correlateAlert: (id: string) =>
    apiFetch<Alert>(`/alerts/${id}/correlate`, { method: 'POST' }),
  investigateAlert: (id: string) =>
    apiFetch<Alert>(`/alerts/${id}/investigate`, { method: 'POST' }),
  generateReport: (id: string) =>
    apiFetch<Report>(`/alerts/${id}/generate-report`, { method: 'POST' }),

  // Investigations
  listInvestigations: () =>
    apiFetch<any>('/investigations').then((d) => asList<Investigation>(d)),
  getInvestigation: (id: string) =>
    apiFetch<Investigation>(`/investigations/${id}`),
  submitFeedback: (id: string, body: Partial<Feedback>) =>
    apiFetch<Feedback>(`/investigations/${id}/feedback`, {
      method: 'POST',
      body,
    }),

  // Reports
  listReports: () => apiFetch<any>('/reports').then((d) => asList<Report>(d)),
  getReport: (id: string) => apiFetch<Report>(`/reports/${id}`),
  getReportMarkdown: (id: string) =>
    apiFetch<string>(`/reports/${id}/markdown`, { raw: true }),
  regenerateReport: (id: string) =>
    apiFetch<Report>(`/reports/${id}/regenerate`, { method: 'POST' }),

  // AI
  listProviders: () =>
    apiFetch<any>('/ai/providers').then((d) =>
      Array.isArray(d?.providers) ? (d.providers as AIProvider[]) : asList<AIProvider>(d)
    ),
  // Full /ai/providers object (default provider, routing mode, fallback chain).
  aiProvidersInfo: () => apiFetch<any>('/ai/providers'),
  aiCapabilities: () => apiFetch<any>('/ai/capabilities'),
  aiModels: () => apiFetch<any>('/ai/models'),
  ollamaModels: () => apiFetch<any>('/ai/ollama/models'),
  getAiConfig: () => apiFetch<any>('/ai/config'),
  updateAiConfig: (body: { default_provider?: string; routing_mode?: string; fallback_enabled?: boolean }) =>
    apiFetch<any>('/ai/config', { method: 'PUT', body }),
  listPrompts: () => apiFetch<any[]>('/ai/prompts'),
  createPrompt: (body: { prompt_type: string; template: string; name?: string }) =>
    apiFetch<any>('/ai/prompts', { method: 'POST', body }),
  activatePrompt: (id: number) =>
    apiFetch<any>(`/ai/prompts/${id}/activate`, { method: 'POST' }),
  testPrompt: (id: number) =>
    apiFetch<any>(`/ai/prompts/${id}/test`, { method: 'POST' }),
  providersHealth: () =>
    apiFetch<any>('/ai/providers/health').then((d) =>
      asList<ProviderHealth>(d)
    ),
  testProvider: (provider: string, body?: any) =>
    apiFetch<ProviderHealth>('/ai/providers/test', {
      method: 'POST',
      body: { provider, ...(body || {}) },
    }),
  listRuns: () => apiFetch<any>('/ai/runs').then((d) => asList<AIRun>(d)),
  usageSummary: () => apiFetch<UsageSummary>('/ai/usage-summary'),
  promptPreview: (body: any) =>
    apiFetch<any>('/ai/prompt-preview', { method: 'POST', body }),

  // Playbooks
  listPlaybooks: () =>
    apiFetch<any>('/playbooks').then((d) => asList<Playbook>(d)),
  getPlaybook: (id: string) => apiFetch<Playbook>(`/playbooks/${id}`),

  // Dashboard
  dashboardSummary: () => apiFetch<DashboardSummary>('/dashboard/summary'),
  dailySummary: () => apiFetch<DailySummary>('/dashboard/daily-summary'),
  mitreSummary: () => apiFetch<MitreSummary>('/dashboard/mitre-summary'),
  aiOperations: () => apiFetch<AIOperationsSummary>('/dashboard/ai-operations'),

  // Allowlists
  listAllowlists: (customerId?: string) => {
    const qs = customerId ? `?customer_id=${customerId}` : '';
    return apiFetch<any>(`/allowlists${qs}`).then((d) => asList<Allowlist>(d));
  },
  createAllowlist: (body: Partial<Allowlist>) =>
    apiFetch<Allowlist>('/allowlists', { method: 'POST', body }),
  deleteAllowlist: (id: string) =>
    apiFetch<void>(`/allowlists/${id}`, { method: 'DELETE' }),

  // Audit
  listAuditLogs: () =>
    apiFetch<any>('/audit-logs').then((d) => asList<AuditLog>(d)),
};
