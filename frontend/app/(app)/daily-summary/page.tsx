'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle, StatCard } from '@/components/ui/misc';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SeverityBadge, VerdictBadge } from '@/components/ui/badge';
import { LoadingState } from '@/components/ui/states';

export default function DailySummaryPage() {
  const q = useQuery({ queryKey: ['daily-summary'], queryFn: () => api.dailySummary() });
  if (q.isLoading) return <LoadingState label="Loading daily summary…" />;
  const d: any = q.data || {};

  return (
    <div className="space-y-5">
      <SectionTitle title="Daily SOC Summary" description={`Rolling ${d.window || '24h'} activity`} />
      <Card><CardHeader><CardTitle>Narrative</CardTitle></CardHeader>
        <CardContent><p className="text-sm leading-relaxed text-muted-foreground">{d.narrative}</p></CardContent></Card>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Alerts (24h)" value={d.alerts ?? 0} />
        <StatCard label="Investigations" value={d.investigations ?? 0} accent="#22c55e" />
        <StatCard label="Verdicts" value={Object.keys(d.verdicts || {}).length} accent="#f59e0b" />
      </div>
      <Card><CardHeader><CardTitle>Recent Highlights</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {(d.highlights || []).map((h: any) => (
              <Link key={h.alert_id} href={`/alerts/${h.alert_id}`} className="flex items-center justify-between rounded-md border border-border px-3 py-2 hover:border-primary/50">
                <span className="text-sm">{h.title}</span>
                <span className="flex items-center gap-2">
                  <SeverityBadge severity={h.severity} />
                  {h.verdict && <VerdictBadge verdict={h.verdict} />}
                </span>
              </Link>
            ))}
            {(d.highlights?.length ?? 0) === 0 && <p className="text-sm text-muted-foreground">No alerts in the last 24h.</p>}
          </div>
        </CardContent></Card>
    </div>
  );
}
