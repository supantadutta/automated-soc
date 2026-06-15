'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Card, CardContent } from '@/components/ui/card';
import { VerdictBadge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { QueryBoundary, EmptyState } from '@/components/ui/states';
import { formatRelative } from '@/lib/utils';

export default function ReportsPage() {
  const q = useQuery({ queryKey: ['reports'], queryFn: () => api.listReports() });
  return (
    <div className="space-y-5">
      <SectionTitle title="Reports" description="Generated SOC investigation reports" />
      <Card>
        <CardContent className="p-0">
          <QueryBoundary
            isLoading={q.isLoading} isError={q.isError} error={q.error} data={q.data}
            isEmpty={(q.data?.length ?? 0) === 0} onRetry={() => q.refetch()}
            empty={<EmptyState title="No reports yet" />}
          >
            {(rows) => (
              <Table>
                <TableHeader><TableRow>
                  <TableHead>Title</TableHead><TableHead>Verdict</TableHead>
                  <TableHead>Confidence</TableHead><TableHead>When</TableHead>
                </TableRow></TableHeader>
                <TableBody>
                  {rows.map((r: any) => (
                    <TableRow key={r.id}>
                      <TableCell><Link href={`/reports/${r.id}`} className="font-medium hover:text-primary">{r.title}</Link></TableCell>
                      <TableCell><VerdictBadge verdict={r.verdict} /></TableCell>
                      <TableCell className="tabular-nums">{r.confidence_score}%</TableCell>
                      <TableCell className="text-muted-foreground">{formatRelative(r.created_at)}</TableCell>
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
