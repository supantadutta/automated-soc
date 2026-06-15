'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Loader2, AlertTriangle, Inbox } from 'lucide-react';
import { Button } from './button';

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn('h-5 w-5 animate-spin text-primary', className)} />;
}

export function LoadingState({ label = 'Loading…', className }: { label?: string; className?: string }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 py-16 text-muted-foreground', className)}>
      <Spinner className="h-6 w-6" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function EmptyState({
  title = 'Nothing here yet',
  description,
  icon,
  action,
  className,
}: {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-card/40 py-16 px-6 text-center',
        className
      )}
    >
      <div className="rounded-full bg-secondary p-3 text-muted-foreground">
        {icon || <Inbox className="h-6 w-6" />}
      </div>
      <div>
        <p className="text-sm font-medium text-foreground">{title}</p>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
  className,
}: {
  error?: unknown;
  onRetry?: () => void;
  className?: string;
}) {
  const message =
    error instanceof Error ? error.message : typeof error === 'string' ? error : 'Something went wrong';
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border border-red-500/30 bg-red-500/5 py-12 px-6 text-center',
        className
      )}
    >
      <div className="rounded-full bg-red-500/15 p-3 text-red-400">
        <AlertTriangle className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm font-medium text-foreground">Could not load data</p>
        <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-pulse rounded-md bg-secondary', className)} />;
}

/**
 * Wrapper that renders loading / error / empty / content states from a react-query-like result.
 */
export function QueryBoundary<T>({
  isLoading,
  isError,
  error,
  data,
  isEmpty,
  onRetry,
  loadingLabel,
  empty,
  children,
}: {
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
  data: T | undefined;
  isEmpty?: boolean;
  onRetry?: () => void;
  loadingLabel?: string;
  empty?: React.ReactNode;
  children: (data: T) => React.ReactNode;
}) {
  if (isLoading) return <LoadingState label={loadingLabel} />;
  if (isError) return <ErrorState error={error} onRetry={onRetry} />;
  if (data === undefined || data === null) return <>{empty ?? <EmptyState />}</>;
  if (isEmpty) return <>{empty ?? <EmptyState />}</>;
  return <>{children(data)}</>;
}
