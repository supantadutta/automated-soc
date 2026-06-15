'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Card, CardContent } from '@/components/ui/card';
import { VerdictBadge, Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { QueryBoundary, EmptyState } from '@/components/ui/states';

const LABELS = ['TP', 'FP', 'Benign', 'Duplicate', 'Escalated', 'Customer Confirmed'];

export default function FeedbackPage() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ['investigations'], queryFn: () => api.listInvestigations() });
  const [done, setDone] = useState<Record<string, string>>({});

  async function send(invId: number, label: string) {
    await api.submitFeedback(String(invId), { ...({ label } as any) });
    setDone((d) => ({ ...d, [invId]: label }));
    qc.invalidateQueries({ queryKey: ['audit'] });
  }

  return (
    <div className="space-y-5">
      <SectionTitle title="Analyst Feedback" description="Confirm or correct AI verdicts — feedback informs future confidence" />
      <QueryBoundary isLoading={q.isLoading} isError={q.isError} error={q.error} data={q.data}
        isEmpty={(q.data?.length ?? 0) === 0} onRetry={() => q.refetch()}
        empty={<EmptyState title="No investigations to review" />}>
        {(rows) => (
          <div className="space-y-3">
            {rows.map((i: any) => (
              <Card key={i.id}>
                <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
                  <div className="flex items-center gap-3">
                    <Link href={`/alerts/${i.alert_id}`} className="font-medium hover:text-primary">Investigation #{i.id} (alert #{i.alert_id})</Link>
                    <VerdictBadge verdict={i.verdict} />
                    <span className="text-xs text-muted-foreground">{i.confidence_score}% · {i.provider}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-1.5">
                    {done[i.id] ? <Badge variant="success">recorded: {done[i.id]}</Badge> : LABELS.map((l) => (
                      <Button key={l} size="sm" variant="outline" onClick={() => send(i.id, l)}>{l}</Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </QueryBoundary>
    </div>
  );
}
