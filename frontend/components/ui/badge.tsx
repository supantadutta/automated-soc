'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

type Variant =
  | 'default'
  | 'secondary'
  | 'outline'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info';

const variants: Record<Variant, string> = {
  default: 'bg-primary/15 text-primary border-primary/30',
  secondary: 'bg-secondary text-secondary-foreground border-border',
  outline: 'bg-transparent text-foreground border-border',
  success: 'bg-green-500/15 text-green-400 border-green-500/30',
  warning: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  danger: 'bg-red-500/15 text-red-400 border-red-500/30',
  info: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

export function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap',
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

// ---- Severity badge -------------------------------------------------------
const SEV_STYLES: Record<string, string> = {
  critical: 'bg-red-500/15 text-red-400 border-red-500/40',
  high: 'bg-orange-500/15 text-orange-400 border-orange-500/40',
  medium: 'bg-amber-500/15 text-amber-400 border-amber-500/40',
  low: 'bg-blue-500/15 text-blue-400 border-blue-500/40',
  informational: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
  info: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
};

export function SeverityBadge({ severity, className }: { severity?: string; className?: string }) {
  const key = (severity || 'informational').toLowerCase();
  const dotColor: Record<string, string> = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-amber-500',
    low: 'bg-blue-500',
    informational: 'bg-slate-400',
    info: 'bg-slate-400',
  };
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium',
        SEV_STYLES[key] || SEV_STYLES.informational,
        className
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', dotColor[key] || 'bg-slate-400')} />
      {severity || 'Informational'}
    </span>
  );
}

// ---- Verdict badge --------------------------------------------------------
export function VerdictBadge({ verdict, className }: { verdict?: string; className?: string }) {
  if (!verdict) {
    return (
      <span
        className={cn(
          'inline-flex items-center rounded-full border border-border bg-secondary px-2 py-0.5 text-xs font-medium text-muted-foreground',
          className
        )}
      >
        Pending
      </span>
    );
  }
  const v = verdict.toLowerCase();
  let style = 'bg-slate-500/15 text-slate-300 border-slate-500/40';
  if (['malicious', 'true positive'].includes(v))
    style = 'bg-red-500/15 text-red-400 border-red-500/40';
  else if (['suspicious', 'escalate'].includes(v))
    style = 'bg-orange-500/15 text-orange-400 border-orange-500/40';
  else if (v === 'inconclusive')
    style = 'bg-amber-500/15 text-amber-400 border-amber-500/40';
  else if (['benign', 'false positive'].includes(v))
    style = 'bg-green-500/15 text-green-400 border-green-500/40';

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
        style,
        className
      )}
    >
      {verdict}
    </span>
  );
}

// ---- Status badge ---------------------------------------------------------
export function StatusBadge({ status, className }: { status?: string; className?: string }) {
  const s = (status || 'new').toLowerCase();
  let variant: Variant = 'secondary';
  if (['new', 'parsing', 'enriching', 'correlating', 'investigating'].includes(s))
    variant = 'info';
  else if (['reported', 'closed'].includes(s)) variant = 'success';
  else if (s === 'error') variant = 'danger';
  return (
    <Badge variant={variant} className={cn('capitalize', className)}>
      {status || 'new'}
    </Badge>
  );
}
