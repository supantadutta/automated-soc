'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  className,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children?: React.ReactNode;
  className?: string;
  footer?: React.ReactNode;
}) {
  React.useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div
        className={cn(
          'relative z-10 w-full max-w-lg rounded-xl border border-border bg-card shadow-2xl',
          className
        )}
      >
        <div className="flex items-start justify-between border-b border-border p-5">
          <div>
            {title && <h3 className="text-base font-semibold">{title}</h3>}
            {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
          </div>
          <button onClick={onClose} className="rounded-md p-1 text-muted-foreground hover:bg-accent">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-5">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-border p-5 pt-4">{footer}</div>}
      </div>
    </div>
  );
}
