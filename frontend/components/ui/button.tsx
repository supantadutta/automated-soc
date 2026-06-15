'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

type Variant = 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'success';
type Size = 'sm' | 'md' | 'lg' | 'icon';

const variants: Record<Variant, string> = {
  default:
    'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm',
  secondary:
    'bg-secondary text-secondary-foreground hover:bg-secondary/80',
  outline:
    'border border-border bg-transparent hover:bg-accent hover:text-accent-foreground',
  ghost: 'hover:bg-accent hover:text-accent-foreground',
  destructive: 'bg-red-600 text-white hover:bg-red-600/90 shadow-sm',
  success: 'bg-green-600 text-white hover:bg-green-600/90 shadow-sm',
};

const sizes: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-9 px-4 text-sm',
  lg: 'h-10 px-6 text-sm',
  icon: 'h-9 w-9',
};

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', loading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background',
          'disabled:pointer-events-none disabled:opacity-50',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
