'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

// ---- Progress / confidence bar -------------------------------------------
export function Progress({
  value = 0,
  className,
  color,
}: {
  value?: number;
  className?: string;
  color?: string;
}) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={cn('h-2 w-full overflow-hidden rounded-full bg-secondary', className)}>
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${pct}%`, backgroundColor: color || 'hsl(var(--primary))' }}
      />
    </div>
  );
}

export function ConfidenceBar({ confidence }: { confidence?: number }) {
  if (confidence === undefined || confidence === null)
    return <span className="text-xs text-muted-foreground">—</span>;
  const pct = confidence <= 1 ? Math.round(confidence * 100) : Math.round(confidence);
  const color = pct >= 80 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-2">
      <Progress value={pct} color={color} className="w-20" />
      <span className="text-xs font-medium tabular-nums text-muted-foreground">{pct}%</span>
    </div>
  );
}

// ---- Switch ---------------------------------------------------------------
export function Switch({
  checked,
  onCheckedChange,
  disabled,
  className,
}: {
  checked?: boolean;
  onCheckedChange?: (v: boolean) => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={!!checked}
      disabled={disabled}
      onClick={() => onCheckedChange?.(!checked)}
      className={cn(
        'relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors disabled:opacity-50',
        checked ? 'bg-primary' : 'bg-secondary',
        className
      )}
    >
      <span
        className={cn(
          'inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform',
          checked ? 'translate-x-4' : 'translate-x-0.5'
        )}
      />
    </button>
  );
}

// ---- Code block -----------------------------------------------------------
export function CodeBlock({
  code,
  language,
  className,
}: {
  code?: string;
  language?: string;
  className?: string;
}) {
  const [copied, setCopied] = React.useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* noop */
    }
  };
  return (
    <div className={cn('relative rounded-lg border border-border bg-[#0b1120]', className)}>
      <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {language || 'text'}
        </span>
        <button
          onClick={copy}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="overflow-x-auto p-3 text-xs leading-relaxed">
        <code className="font-mono text-slate-200">{code || '// no content'}</code>
      </pre>
    </div>
  );
}

// ---- Key/value list -------------------------------------------------------
export function KeyValue({ items }: { items: { label: string; value: React.ReactNode }[] }) {
  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
      {items.map((it, i) => (
        <div key={i} className="flex flex-col gap-0.5">
          <dt className="text-xs uppercase tracking-wide text-muted-foreground">{it.label}</dt>
          <dd className="text-sm font-medium text-foreground break-all">{it.value ?? '—'}</dd>
        </div>
      ))}
    </dl>
  );
}

// ---- Stat card ------------------------------------------------------------
export function StatCard({
  label,
  value,
  icon,
  hint,
  accent,
}: {
  label: string;
  value: React.ReactNode;
  icon?: React.ReactNode;
  hint?: string;
  accent?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
          <p className="mt-2 text-2xl font-bold tabular-nums">{value}</p>
          {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
        </div>
        {icon && (
          <div
            className="rounded-lg p-2"
            style={{ backgroundColor: (accent || 'hsl(var(--primary))') + '22', color: accent || 'hsl(var(--primary))' }}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

// ---- Section header -------------------------------------------------------
export function SectionTitle({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4">
      <div>
        <h2 className="text-lg font-semibold">{title}</h2>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  );
}
