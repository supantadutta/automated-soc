'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { QueryBoundary, EmptyState } from '@/components/ui/states';
import { formatDate } from '@/lib/utils';

export default function AuditPage() {
  const q = useQuery({ queryKey: ['audit'], queryFn: () => api.listAuditLogs() });
  return (
    <div className="space-y-5">
      <SectionTitle title="Audit Log" description="Immutable record of all significant actions" />
      <Card>
        <CardContent className="p-0">
          <QueryBoundary isLoading={q.isLoading} isError={q.isError} error={q.error} data={q.data}
            isEmpty={(q.data?.length ?? 0) === 0} onRetry={() => q.refetch()}
            empty={<EmptyState title="No audit entries" />}>
            {(rows) => (
              <Table>
                <TableHeader><TableRow>
                  <TableHead>Action</TableHead><TableHead>Actor</TableHead>
                  <TableHead>Target</TableHead><TableHead>When</TableHead>
                </TableRow></TableHeader>
                <TableBody>
                  {rows.map((l: any) => (
                    <TableRow key={l.id}>
                      <TableCell><Badge variant="outline">{l.action}</Badge></TableCell>
                      <TableCell className="text-muted-foreground">{l.actor_email || '—'}</TableCell>
                      <TableCell className="text-muted-foreground">{l.target_type ? `${l.target_type} #${l.target_id}` : '—'}</TableCell>
                      <TableCell className="text-muted-foreground">{formatDate(l.created_at)}</TableCell>
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
