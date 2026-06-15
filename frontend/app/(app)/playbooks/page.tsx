'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { QueryBoundary, EmptyState } from '@/components/ui/states';

export default function PlaybooksPage() {
  const q = useQuery({ queryKey: ['playbooks'], queryFn: () => api.listPlaybooks() });
  return (
    <div className="space-y-5">
      <SectionTitle title="Playbooks" description="Built-in SOC triage & investigation playbooks (containment is human-approved)" />
      <QueryBoundary isLoading={q.isLoading} isError={q.isError} error={q.error} data={q.data}
        isEmpty={(q.data?.length ?? 0) === 0} onRetry={() => q.refetch()}
        empty={<EmptyState title="No playbooks" />}>
        {(rows) => (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {rows.map((p: any) => (
              <Card key={p.id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    {p.name}
                    <Badge variant="secondary">{p.category}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="mb-3 text-sm text-muted-foreground">{p.description}</p>
                  <Tabs defaultValue="triage">
                    <TabsList>
                      <TabsTrigger value="triage">Triage</TabsTrigger>
                      <TabsTrigger value="investigation">Investigation</TabsTrigger>
                      <TabsTrigger value="containment">Containment</TabsTrigger>
                    </TabsList>
                    <TabsContent value="triage"><StepList steps={p.triage_steps} /></TabsContent>
                    <TabsContent value="investigation"><StepList steps={p.investigation_steps} /></TabsContent>
                    <TabsContent value="containment"><StepList steps={p.containment_steps} /></TabsContent>
                  </Tabs>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {(p.mitre_techniques || []).map((t: string) => <Badge key={t} variant="outline">{t}</Badge>)}
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

function StepList({ steps }: { steps?: string[] }) {
  if (!steps?.length) return <p className="text-sm text-muted-foreground">No steps.</p>;
  return <ol className="list-decimal space-y-1 pl-5 text-sm text-muted-foreground">{steps.map((s, i) => <li key={i}>{s}</li>)}</ol>;
}
