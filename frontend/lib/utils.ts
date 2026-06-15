import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value?: string | number | Date | null): string {
  if (!value) return '—';
  const d = new Date(value);
  if (isNaN(d.getTime())) return String(value);
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelative(value?: string | number | Date | null): string {
  if (!value) return '—';
  const d = new Date(value);
  if (isNaN(d.getTime())) return String(value);
  const diff = Date.now() - d.getTime();
  const sec = Math.round(diff / 1000);
  const min = Math.round(sec / 60);
  const hr = Math.round(min / 60);
  const day = Math.round(hr / 24);
  if (sec < 60) return `${sec}s ago`;
  if (min < 60) return `${min}m ago`;
  if (hr < 24) return `${hr}h ago`;
  if (day < 30) return `${day}d ago`;
  return formatDate(value);
}

export function formatNumber(n?: number | null): string {
  if (n === undefined || n === null || isNaN(n)) return '0';
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (Math.abs(n) >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(n);
}

export function formatCost(n?: number | null): string {
  if (n === undefined || n === null || isNaN(n)) return '$0.00';
  if (n < 0.01 && n > 0) return '$' + n.toFixed(4);
  return '$' + n.toFixed(2);
}

export function formatTokens(n?: number | null): string {
  return formatNumber(n) + ' tok';
}

export function severityColor(sev?: string): string {
  switch ((sev || '').toLowerCase()) {
    case 'critical':
      return '#ef4444';
    case 'high':
      return '#f97316';
    case 'medium':
      return '#f59e0b';
    case 'low':
      return '#3b82f6';
    case 'informational':
    case 'info':
      return '#64748b';
    default:
      return '#64748b';
  }
}

export function verdictColor(v?: string): string {
  switch ((v || '').toLowerCase()) {
    case 'malicious':
    case 'true positive':
      return '#ef4444';
    case 'suspicious':
    case 'escalate':
      return '#f97316';
    case 'inconclusive':
      return '#f59e0b';
    case 'benign':
    case 'false positive':
      return '#22c55e';
    default:
      return '#64748b';
  }
}

export const CHART_COLORS = [
  '#0ea5e9',
  '#8b5cf6',
  '#22c55e',
  '#f59e0b',
  '#ef4444',
  '#ec4899',
  '#14b8a6',
  '#f97316',
];

export function truncate(s?: string, n = 80): string {
  if (!s) return '';
  return s.length > n ? s.slice(0, n) + '…' : s;
}

export function safeJson(value: any): string {
  if (value === undefined || value === null) return '';
  if (typeof value === 'string') {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function initials(name?: string): string {
  if (!name) return '?';
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
}
