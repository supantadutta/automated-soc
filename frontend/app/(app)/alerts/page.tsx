'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { SeverityBadge, VerdictBadge, StatusBadge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { QueryBoundary, EmptyState } from '@/components/ui/states';
import { formatRelative } from '@/lib/utils';

export default function AlertsPage() {
  const q = useQuery({ queryKey: ['alerts'], queryFn: () => api.listAlerts() });

  return (
    <div className="space-y-5">
      <SectionTitle
        title="Alert Inbox"
        description="All ingested SOC alerts across customers"
        action={
          <Link href="/alerts/submit">
            <Button>Submit Alert</Button>
          </Link>
        }
      />
      <Card>
        <CardContent className="p-0">
          <QueryBoundary
            isLoading={q.isLoading}
            isError={q.isError}
            error={q.error}
            data={q.data}
            isEmpty={(q.data?.length ?? 0) === 0}
            onRetry={() => q.refetch()}
            empty={
              <EmptyState
                title="No alerts yet"
                description="Submit an alert or run the backend seed to load 20 demo alerts."
              />
            }
          >
            {(alerts) => (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Alert</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>AI Verdict</TableHead>
                    <TableHead>Conf.</TableHead>
                    <TableHead>Provider</TableHead>
                    <TableHead>When</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alerts.map((a: any) => (
                    <TableRow key={a.id} className="cursor-pointer">
                      <TableCell>
                        <Link href={`/alerts/${a.id}`} className="font-medium hover:text-primary">
                          {a.title || a.name}
                        </Link>
                      </TableCell>
                      <TableCell><SeverityBadge severity={a.severity} /></TableCell>
                      <TableCell className="text-muted-foreground">{a.source_tool || '—'}</TableCell>
                      <TableCell className="text-muted-foreground">{a.category || '—'}</TableCell>
                      <TableCell><StatusBadge status={a.status} /></TableCell>
                      <TableCell>{a.ai_verdict ? <VerdictBadge verdict={a.ai_verdict} /> : <span className="text-muted-foreground">—</span>}</TableCell>
                      <TableCell className="tabular-nums">{a.ai_confidence != null ? `${a.ai_confidence}%` : '—'}</TableCell>
                      <TableCell className="text-muted-foreground">{a.ai_provider || '—'}</TableCell>
                      <TableCell className="text-muted-foreground">{formatRelative(a.created_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </QueryBoundary>
        </CardContent>
      </Card>
    </div>
  );
}
