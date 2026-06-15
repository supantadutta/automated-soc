'use client';

import { useQuery } from '@tanstack/react-query';
import { Cpu, Zap, DollarSign, AlertTriangle, Server } from 'lucide-react';
import { api } from '@/lib/api';
import { StatCard, SectionTitle } from '@/components/ui/misc';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DonutChart, HorizontalBarChart } from '@/components/charts/charts';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { LoadingState } from '@/components/ui/states';
import { formatCost, formatRelative } from '@/lib/utils';

export default function AIOperationsPage() {
  const ops = useQuery({ queryKey: ['ai-operations'], queryFn: () => api.aiOperations() });
  const health = useQuery({ queryKey: ['providers-health'], queryFn: () => api.providersHealth() });

  if (ops.isLoading) return <LoadingState label="Loading AI operations…" />;
  const d: any = ops.data || {};
  const byProvider = d.by_provider ? Object.entries(d.by_provider).map(([provider, runs]) => ({ provider, runs })) : [];
  const localCloud = [
    { name: 'Local', count: d.local_requests || 0 },
    { name: 'Cloud', count: d.cloud_requests || 0 },
  ];

  return (
    <div className="space-y-6">
      <SectionTitle
        title="AI Operations"
        description={`Active provider: ${d.active_provider} · mode ${d.routing_mode} · fallback: ${(d.fallback_chain || []).join(' → ')}`}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard label="Total Runs" value={d.total_runs ?? 0} icon={<Cpu className="h-5 w-5" />} />
        <StatCard label="Avg Latency" value={`${d.avg_latency_ms ?? 0}ms`} icon={<Zap className="h-5 w-5" />} accent="#22c55e" />
        <StatCard label="Est. Cost" value={formatCost(d.estimated_cost)} icon={<DollarSign className="h-5 w-5" />} accent="#f59e0b" />
        <StatCard label="Failed" value={d.failed ?? 0} icon={<AlertTriangle className="h-5 w-5" />} accent="#ef4444" />
        <StatCard label="Fallbacks" value={d.fallback_used ?? 0} icon={<Server className="h-5 w-5" />} accent="#a855f7" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card><CardHeader><CardTitle>Requests by Provider</CardTitle></CardHeader>
          <CardContent><HorizontalBarChart data={byProvider} categoryKey="provider" valueKey="runs" /></CardContent></Card>
        <Card><CardHeader><CardTitle>Local vs Cloud</CardTitle></CardHeader>
          <CardContent><DonutChart data={localCloud} nameKey="name" valueKey="count" /></CardContent></Card>
      </div>

      <Card><CardHeader><CardTitle>Provider Health</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {(health.data || []).map((h: any) => (
              <div key={h.provider} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{h.provider}</span>
                  {h.is_local && <Badge variant="outline">local</Badge>}
                </div>
                <Badge variant={h.healthy ? 'success' : h.configured ? 'danger' : 'secondary'}>
                  {h.healthy ? 'healthy' : h.configured ? 'down' : 'not configured'}
                </Badge>
              </div>
            ))}
            {(health.data?.length ?? 0) === 0 && <p className="text-sm text-muted-foreground">Only the mock provider is configured.</p>}
          </div>
        </CardContent></Card>

      <Card><CardHeader><CardTitle>Last 20 AI Runs</CardTitle></CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader><TableRow>
              <TableHead>Provider</TableHead><TableHead>Model</TableHead><TableHead>Type</TableHead>
              <TableHead>Tokens</TableHead><TableHead>Cost</TableHead><TableHead>Latency</TableHead>
              <TableHead>Status</TableHead><TableHead>When</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {(d.recent_runs || []).map((r: any) => (
                <TableRow key={r.id}>
                  <TableCell>{r.provider} {r.is_local && <Badge variant="outline">local</Badge>}</TableCell>
                  <TableCell className="text-muted-foreground">{r.model || '—'}</TableCell>
                  <TableCell className="text-muted-foreground">{r.prompt_type || '—'}</TableCell>
                  <TableCell className="tabular-nums">{(r.input_tokens || 0) + (r.output_tokens || 0)}</TableCell>
                  <TableCell className="tabular-nums">{formatCost(r.estimated_cost)}</TableCell>
                  <TableCell className="tabular-nums">{r.latency_ms}ms</TableCell>
                  <TableCell><Badge variant={r.success ? 'success' : 'danger'}>{r.success ? 'ok' : 'error'}</Badge></TableCell>
                  <TableCell className="text-muted-foreground">{formatRelative(r.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {(d.recent_runs?.length ?? 0) === 0 && <p className="p-4 text-sm text-muted-foreground">No AI runs yet. Investigate an alert to populate.</p>}
        </CardContent></Card>
    </div>
  );
}
