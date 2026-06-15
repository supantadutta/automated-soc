'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Card, CardContent } from '@/components/ui/card';
import { VerdictBadge, Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { QueryBoundary, EmptyState } from '@/components/ui/states';
import { formatRelative } from '@/lib/utils';

export default function InvestigationsPage() {
  const q = useQuery({ queryKey: ['investigations'], queryFn: () => api.listInvestigations() });
  return (
    <div className="space-y-5">
      <SectionTitle title="Investigations" description="AI-assisted investigation results" />
      <Card>
        <CardContent className="p-0">
          <QueryBoundary
            isLoading={q.isLoading} isError={q.isError} error={q.error} data={q.data}
            isEmpty={(q.data?.length ?? 0) === 0} onRetry={() => q.refetch()}
            empty={<EmptyState title="No investigations yet" />}
          >
            {(rows) => (
              <Table>
                <TableHeader><TableRow>
                  <TableHead>ID</TableHead><TableHead>Alert</TableHead><TableHead>Verdict</TableHead>
                  <TableHead>Confidence</TableHead><TableHead>Severity</TableHead><TableHead>Provider</TableHead>
                  <TableHead>Fallback</TableHead><TableHead>When</TableHead>
                </TableRow></TableHeader>
                <TableBody>
                  {rows.map((i: any) => (
                    <TableRow key={i.id}>
                      <TableCell>#{i.id}</TableCell>
                      <TableCell><Link href={`/alerts/${i.alert_id}`} className="text-primary hover:underline">alert #{i.alert_id}</Link></TableCell>
                      <TableCell><VerdictBadge verdict={i.verdict} /></TableCell>
                      <TableCell className="tabular-nums">{i.confidence_score}%</TableCell>
                      <TableCell className="text-muted-foreground">{i.severity_recommendation || '—'}</TableCell>
                      <TableCell className="text-muted-foreground">{i.provider}/{i.model}</TableCell>
                      <TableCell>{i.fallback_used ? <Badge variant="outline">fallback</Badge> : '—'}</TableCell>
                      <TableCell className="text-muted-foreground">{formatRelative(i.created_at)}</TableCell>
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
