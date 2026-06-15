// Shared TypeScript types for AutoSOC Command Center

export type Severity = 'Critical' | 'High' | 'Medium' | 'Low' | 'Informational';
export type Verdict =
  | 'True Positive'
  | 'False Positive'
  | 'Benign'
  | 'Suspicious'
  | 'Malicious'
  | 'Inconclusive'
  | 'Escalate';
export type AlertStatus =
  | 'new'
  | 'parsing'
  | 'enriching'
  | 'correlating'
  | 'investigating'
  | 'reported'
  | 'closed'
  | 'error';

export interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type?: string;
}

export interface Customer {
  id: string;
  name: string;
  description?: string;
  industry?: string;
  tier?: string;
  contact_email?: string;
  alert_count?: number;
  open_alerts?: number;
  created_at?: string;
  updated_at?: string;
}

export interface AIPolicy {
  customer_id?: string;
  routing_mode?: 'local-only' | 'cloud-only' | 'hybrid' | 'cost-optimized';
  privacy_mode?: boolean;
  allowed_providers?: string[];
  preferred_provider?: string;
  preferred_model?: string;
  max_cost_per_alert?: number;
  auto_investigate?: boolean;
  auto_report?: boolean;
  pii_redaction?: boolean;
  data_residency?: string;
  updated_at?: string;
}

export interface Allowlist {
  id: string;
  customer_id?: string;
  type: 'ip' | 'domain' | 'hash' | 'user' | 'process';
  value: string;
  reason?: string;
  created_by?: string;
  created_at?: string;
}

export interface IOC {
  type: 'ip' | 'domain' | 'url' | 'hash' | 'email' | 'file' | string;
  value: string;
  verdict?: Verdict | string;
  score?: number;
  reputation?: string;
  source?: string;
  tags?: string[];
  enriched?: boolean;
  details?: Record<string, any>;
}

export interface ParsedFields {
  source_ip?: string;
  dest_ip?: string;
  username?: string;
  hostname?: string;
  process?: string;
  command_line?: string;
  file_hash?: string;
  domain?: string;
  url?: string;
  event_type?: string;
  [key: string]: any;
}

export interface MitreTechnique {
  id: string; // e.g. T1059
  name: string;
  tactic: string; // e.g. Execution
  tactic_id?: string; // e.g. TA0002
  description?: string;
  confidence?: number;
  url?: string;
}

export interface DetectionQuery {
  language: 'KQL' | 'SPL' | 'Sigma' | 'EQL' | 'SQL' | string;
  title?: string;
  query: string;
  description?: string;
}

export interface Alert {
  id: string;
  name: string;
  title?: string;
  description?: string;
  severity: Severity;
  status: AlertStatus | string;
  source_tool?: string;
  customer_id?: string;
  customer_name?: string;
  source_ip?: string;
  dest_ip?: string;
  username?: string;
  hostname?: string;
  raw?: string | Record<string, any>;
  raw_alert?: string | Record<string, any>;
  parsed_fields?: ParsedFields;
  iocs?: IOC[];
  ai_verdict?: Verdict | string;
  confidence?: number;
  confidence_score?: number;
  provider?: string;
  model?: string;
  mitre?: MitreTechnique[];
  detection_queries?: DetectionQuery[];
  investigation_id?: string;
  report_id?: string;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface CorrelationItem {
  alert_id: string;
  alert_name?: string;
  relation?: string;
  score?: number;
  reason?: string;
  created_at?: string;
}

export interface Investigation {
  id: string;
  alert_id?: string;
  alert_name?: string;
  customer_name?: string;
  title?: string;
  summary?: string;
  verdict?: Verdict | string;
  confidence?: number;
  severity?: Severity;
  status?: string;
  narrative?: string;
  hypothesis?: string;
  evidence?: string[];
  recommended_actions?: string[];
  next_steps?: string[];
  mitre?: MitreTechnique[];
  provider?: string;
  model?: string;
  tokens_used?: number;
  cost?: number;
  feedback?: Feedback[];
  created_at?: string;
  updated_at?: string;
}

export interface Feedback {
  id?: string;
  investigation_id?: string;
  rating?: 'up' | 'down' | number;
  verdict_correct?: boolean;
  corrected_verdict?: string;
  comment?: string;
  analyst?: string;
  created_at?: string;
}

export interface Report {
  id: string;
  alert_id?: string;
  investigation_id?: string;
  title?: string;
  customer_name?: string;
  severity?: Severity;
  verdict?: Verdict | string;
  status?: string;
  summary?: string;
  markdown?: string;
  format?: string;
  provider?: string;
  model?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AIProvider {
  id: string;
  name: string; // openai, anthropic, ollama ...
  display_name?: string;
  configured: boolean;
  enabled?: boolean;
  type?: 'cloud' | 'local';
  active_model?: string;
  models?: string[];
  health?: 'healthy' | 'degraded' | 'down' | 'unknown' | string;
  latency_ms?: number;
  privacy_mode?: boolean;
  base_url?: string;
  cost_per_1k_input?: number;
  cost_per_1k_output?: number;
  total_cost?: number;
  total_tokens?: number;
  total_runs?: number;
  last_used?: string;
}

export interface ProviderHealth {
  provider: string;
  status: string;
  latency_ms?: number;
  message?: string;
  checked_at?: string;
}

export interface AIRun {
  id: string;
  provider: string;
  model: string;
  task?: string; // parse, enrich, investigate, report ...
  alert_id?: string;
  customer_name?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  cost?: number;
  latency_ms?: number;
  status?: 'success' | 'error' | string;
  local?: boolean;
  created_at?: string;
}

export interface UsageSummary {
  total_runs?: number;
  total_tokens?: number;
  total_cost?: number;
  avg_latency_ms?: number;
  local_runs?: number;
  cloud_runs?: number;
  by_provider?: { provider: string; runs: number; tokens: number; cost: number }[];
  by_task?: { task: string; runs: number; tokens: number; cost: number }[];
  daily?: { date: string; tokens: number; cost: number; runs: number }[];
}

export interface Playbook {
  id: string;
  name: string;
  description?: string;
  category?: string;
  trigger?: string;
  steps?: PlaybookStep[];
  tags?: string[];
  enabled?: boolean;
  created_at?: string;
}

export interface PlaybookStep {
  order?: number;
  name: string;
  action?: string;
  description?: string;
  automated?: boolean;
}

export interface DashboardSummary {
  total_alerts?: number;
  open_alerts?: number;
  critical_alerts?: number;
  investigations?: number;
  reports?: number;
  true_positives?: number;
  false_positives?: number;
  customers?: number;
  avg_response_time_min?: number;
  automation_rate?: number;
  alert_volume?: { date: string; count: number }[];
  severity_breakdown?: { severity: string; count: number }[];
  verdict_distribution?: { verdict: string; count: number }[];
  recent_alerts?: Alert[];
}

export interface DailySummary {
  date?: string;
  total_alerts?: number;
  by_severity?: { severity: string; count: number }[];
  by_verdict?: { verdict: string; count: number }[];
  highlights?: string[];
  narrative?: string;
  top_threats?: { name: string; count: number }[];
}

export interface MitreSummary {
  tactics?: { tactic: string; tactic_id?: string; count: number }[];
  techniques?: { id: string; name: string; tactic: string; count: number }[];
}

export interface AIOperationsSummary extends UsageSummary {
  providers?: AIProvider[];
}

export interface AuditLog {
  id: string;
  action: string;
  actor?: string;
  user?: string;
  entity_type?: string;
  entity_id?: string;
  details?: string | Record<string, any>;
  ip_address?: string;
  created_at?: string;
  timestamp?: string;
}
