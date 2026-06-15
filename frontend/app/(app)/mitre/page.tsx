'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { HorizontalBarChart } from '@/components/charts/charts';
import { LoadingState, EmptyState } from '@/components/ui/states';

export default function MitrePage() {
  const q = useQuery({ queryKey: ['mitre-summary'], queryFn: () => api.mitreSummary() });
  if (q.isLoading) return <LoadingState label="Loading MITRE summary…" />;
  const d: any = q.data || {};
  const tactics = d.tactics ? Object.entries(d.tactics).map(([tactic, count]) => ({ tactic, count })) : [];
  const techniques = d.techniques ? Object.entries(d.techniques).map(([technique, count]) => ({ technique, count })) : [];

  return (
    <div className="space-y-5">
      <SectionTitle title="MITRE ATT&CK Summary" description="Tactics & techniques observed across investigations" />
      {tactics.length === 0 ? (
        <EmptyState title="No MITRE data yet" description="Investigate alerts to populate ATT&CK mappings." />
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card><CardHeader><CardTitle>Tactics</CardTitle></CardHeader>
            <CardContent><HorizontalBarChart data={tactics} categoryKey="tactic" valueKey="count" /></CardContent></Card>
          <Card><CardHeader><CardTitle>Top Techniques</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {techniques.map((t: any) => (
                  <div key={t.technique} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                    <span>{t.technique}</span>
                    <Badge>{t.count}</Badge>
                  </div>
                ))}
              </div>
            </CardContent></Card>
        </div>
      )}
    </div>
  );
}
