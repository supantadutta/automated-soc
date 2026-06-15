'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { VerdictBadge } from '@/components/ui/badge';
import { LoadingState, ErrorState } from '@/components/ui/states';

export default function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const meta = useQuery({ queryKey: ['report', id], queryFn: () => api.getReport(id) });
  const md = useQuery({ queryKey: ['report-md', id], queryFn: () => api.getReportMarkdown(id) });

  if (meta.isLoading || md.isLoading) return <LoadingState label="Loading report…" />;
  if (meta.isError) return <ErrorState error={meta.error} onRetry={() => meta.refetch()} />;
  const r: any = meta.data || {};

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <Link href="/reports" className="text-xs text-muted-foreground hover:text-foreground">← Back to reports</Link>
          <h1 className="mt-1 flex items-center gap-2 text-xl font-bold">{r.title} <VerdictBadge verdict={r.verdict} /></h1>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigator.clipboard.writeText(md.data || '')}>Copy Markdown</Button>
          <Button variant="secondary" onClick={() => api.regenerateReport(id).then(() => { qc.invalidateQueries({ queryKey: ['report-md', id] }); md.refetch(); })}>Regenerate</Button>
        </div>
      </div>
      <Card><CardContent className="p-5">
        <pre className="whitespace-pre-wrap break-words text-sm leading-relaxed">{md.data}</pre>
      </CardContent></Card>
    </div>
  );
}
