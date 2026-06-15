'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ShieldAlert, Search, FileWarning, Activity } from 'lucide-react';
import { api } from '@/lib/api';
import { StatCard, SectionTitle } from '@/components/ui/misc';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarBreakdownChart, DonutChart, HorizontalBarChart } from '@/components/charts/charts';
import { LoadingState, ErrorState } from '@/components/ui/states';
import { Button } from '@/components/ui/button';

function toArray(obj?: Record<string, number>) {
  if (!obj) return [];
  return Object.entries(obj).map(([name, count]) => ({ name, count }));
}

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => api.dashboardSummary(),
  });
  const mitre = useQuery({ queryKey: ['mitre-summary'], queryFn: () => api.mitreSummary() });

  if (isLoading) return <LoadingState label="Loading dashboard…" />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;

  const d: any = data || {};
  const severity = toArray(d.severity_breakdown);
  const verdicts = toArray(d.verdict_distribution);
  const categories = toArray(d.top_categories);
  const tactics = mitre.data?.tactics
    ? Object.entries(mitre.data.tactics as any).map(([tactic, count]) => ({ tactic, count }))
    : [];

  return (
    <div className="space-y-6">
      <SectionTitle
        title="SOC Dashboard"
        description="Operational overview across all customers"
        action={
          <Link href="/alerts/submit">
            <Button>Submit Alert</Button>
          </Link>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Alerts" value={d.total_alerts ?? 0} icon={<ShieldAlert className="h-5 w-5" />} />
        <StatCard label="Open Alerts" value={d.open_alerts ?? 0} icon={<Activity className="h-5 w-5" />} accent="#f59e0b" />
        <StatCard label="Investigations" value={d.total_investigations ?? 0} icon={<Search className="h-5 w-5" />} accent="#22c55e" />
        <StatCard label="Needs Review" value={d.needs_review ?? 0} icon={<FileWarning className="h-5 w-5" />} accent="#ef4444" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Severity Breakdown</CardTitle></CardHeader>
          <CardContent>
            <BarBreakdownChart data={severity} xKey="name" yKey="count" colorBy="severity" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Verdict Distribution</CardTitle></CardHeader>
          <CardContent>
            <DonutChart data={verdicts} nameKey="name" valueKey="count" colorBy="verdict" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Top Alert Categories</CardTitle></CardHeader>
          <CardContent>
            <HorizontalBarChart data={categories} categoryKey="name" valueKey="count" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>MITRE Tactics Observed</CardTitle></CardHeader>
          <CardContent>
            <HorizontalBarChart data={tactics} categoryKey="tactic" valueKey="count" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
