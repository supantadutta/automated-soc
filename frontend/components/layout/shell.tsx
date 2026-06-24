'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ShieldCheck, LogOut, Cpu, Menu } from 'lucide-react';
import { NAV_ITEMS, NAV_GROUPS } from './nav-items';
import { api } from '@/lib/api';
import { isAuthenticated, logout } from '@/lib/auth';
import { cn } from '@/lib/utils';

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
    } else {
      setReady(true);
    }
  }, [router]);

  const { data: providerInfo } = useQuery({
    queryKey: ['ai-providers-info'],
    queryFn: () => api.aiProvidersInfo(),
    enabled: ready,
  });
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => api.me(),
    enabled: ready,
  });

  if (!ready) return null;

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 w-64 transform border-r border-border bg-card transition-transform md:static md:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-14 items-center gap-2 border-b border-border px-4">
          <div className="rounded-lg bg-primary/15 p-1.5 text-primary">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <p className="text-sm font-bold">AutoSOC</p>
            <p className="text-[10px] text-muted-foreground">Command Center</p>
          </div>
        </div>
        <nav className="flex-1 space-y-5 overflow-y-auto p-3">
          {NAV_GROUPS.map((group) => (
            <div key={group}>
              <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {group}
              </p>
              <div className="space-y-0.5">
                {NAV_ITEMS.filter((i) => i.group === group).map((item) => {
                  const Icon = item.icon;
                  const active = pathname === item.href || pathname.startsWith(item.href + '/');
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setOpen(false)}
                      className={cn(
                        'flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors',
                        active
                          ? 'bg-primary/15 font-medium text-primary'
                          : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-4 border-b border-border bg-background/80 px-4 backdrop-blur">
          <button className="md:hidden" onClick={() => setOpen((v) => !v)}>
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Cpu className="h-4 w-4 text-primary" />
            <span>
              AI:{' '}
              <span className="font-medium text-foreground">
                {providerInfo?.default_provider || 'mock'}
              </span>{' '}
              · {providerInfo?.default_model || 'mock-soc-1'} · mode{' '}
              <span className="text-foreground">{providerInfo?.routing_mode || 'auto'}</span>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-muted-foreground sm:inline">
              {me?.email}
            </span>
            <button
              onClick={async () => {
                // Revoke server-side (bumps token_version) then clear locally.
                try { await api.logout(); } catch { /* token may already be invalid */ }
                logout();
                router.replace('/login');
              }}
              className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          </div>
        </header>
        <main className="flex-1 p-5">{children}</main>
      </div>
    </div>
  );
}
