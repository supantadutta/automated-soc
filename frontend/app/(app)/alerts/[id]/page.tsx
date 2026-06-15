'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { SeverityBadge, VerdictBadge, StatusBadge, Badge } from '@/components/ui/badge';
import { CodeBlock, KeyValue, ConfidenceBar } from '@/components/ui/misc';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/states';
import { Input, Select, Textarea, Label } from '@/components/ui/input';
import { formatRelative } from '@/lib/utils';

export default function AlertDetailPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [busy, setBusy] = useState<string | null>(null);
  const [correlation, setCorrelation] = useState<any>(null);
  const [provider, setProvider] = useState('');
  const [feedback, setFeedback] = useState('TP');
  const [comment, setComment] = useState('');

  const alertQ = useQuery({ queryKey: ['alert', id], queryFn: () => api.getAlert(id) });
  const invsQ = useQuery({ queryKey: ['investigations'], queryFn: () => api.listInvestigations() });
  const reportsQ = useQuery({ queryKey: ['reports'], queryFn: () => api.listReports() });
  const auditQ = useQuery({ queryKey: ['audit'], queryFn: () => api.listAuditLogs() });

  if (alertQ.isLoading) return <LoadingState label="Loading alert…" />;
  if (alertQ.isError) return <ErrorState error={alertQ.error} onRetry={() => alertQ.refetch()} />;

  const alert: any = alertQ.data || {};
  const investigation: any = (invsQ.data || [])
    .filter((i: any) => i.alert_id === alert.id)
    .sort((a: any, b: any) => (b.id || 0) - (a.id || 0))[0];
  const result: any = investigation?.result || {};
  const report: any = (reportsQ.data || []).filter((r: any) => r.alert_id === alert.id).slice(-1)[0];
  const dq: any = result.detection_query_suggestions || {};

  async function run(step: string, fn: () => Promise<any>) {
    setBusy(step);
    try {
      const res = await fn();
      if (step === 'correlate') setCorrelation(res);
      await qc.invalidateQueries({ queryKey: ['alert', id] });
      await qc.invalidateQueries({ queryKey: ['investigations'] });
      await qc.invalidateQueries({ queryKey: ['reports'] });
      await qc.invalidateQueries({ queryKey: ['audit'] });
    } catch {
      // Pipeline step errors surface via the unchanged alert state; the user can retry.
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link href="/alerts" className="text-xs text-muted-foreground hover:text-foreground">← Back to alerts</Link>
          <h1 className="mt-1 text-xl font-bold">{alert.title}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <SeverityBadge severity={alert.severity} />
            <StatusBadge status={alert.status} />
            {alert.ai_verdict && <VerdictBadge verdict={alert.ai_verdict} />}
            <Badge variant="outline">{alert.source_tool || 'unknown tool'}</Badge>
            {alert.category && <Badge variant="secondary">{alert.category}</Badge>}
            <span className="text-xs text-muted-foreground">{formatRelative(alert.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Pipeline action bar */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-2 p-4">
          <Button size="sm" variant="outline" loading={busy === 'parse'} onClick={() => run('parse', () => api.parseAlert(id))}>1. Parse</Button>
          <Button size="sm" variant="outline" loading={busy === 'enrich'} onClick={() => run('enrich', () => api.enrichAlert(id))}>2. Enrich</Button>
          <Button size="sm" variant="outline" loading={busy === 'correlate'} onClick={() => run('correlate', () => api.correlateAlert(id))}>3. Correlate</Button>
          <Select value={provider} onChange={(e) => setProvider(e.target.value)} className="h-8 w-36 text-xs">
            <option value="">Auto provider</option>
            {['mock', 'ollama', 'lmstudio', 'vllm', 'openai', 'anthropic', 'gemini', 'groq', 'openrouter'].map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </Select>
          <Button size="sm" loading={busy === 'investigate'} onClick={() => run('investigate', () => api.investigateAlert(id))}>4. Investigate</Button>
          <Button size="sm" variant="secondary" loading={busy === 'report'} onClick={() => run('report', () => api.generateReport(id))}>5. Generate Report</Button>
        </CardContent>
      </Card>

      <Tabs defaultValue="overview">
        <TabsList>
          {['overview', 'raw', 'parsed', 'enrichment', 'correlation', 'investigation', 'mitre', 'detection', 'report', 'feedback', 'audit'].map((t) => (
            <TabsTrigger key={t} value={t}>{labels[t]}</TabsTrigger>
          ))}
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {investigation ? (
                  <>
                    <div className="flex items-center gap-3">
                      <VerdictBadge verdict={investigation.verdict} />
                      <span className="text-sm text-muted-foreground">via {investigation.provider}/{investigation.model}</span>
                    </div>
                    <ConfidenceBar confidence={investigation.confidence_score} />
                    <p className="text-sm text-muted-foreground">{result.executive_summary}</p>
                  </>
                ) : (
                  <EmptyState title="Not investigated yet" description="Run the pipeline above." />
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Key Entities</CardTitle></CardHeader>
              <CardContent>
                <KeyValue items={[
                  { label: 'Source IP', value: alert.normalized?.src_ip },
                  { label: 'Destination IP', value: alert.normalized?.dest_ip },
                  { label: 'Username', value: alert.normalized?.username },
                  { label: 'Hostname', value: alert.normalized?.hostname },
                  { label: 'Domain', value: alert.normalized?.domain },
                  { label: 'File Hash', value: alert.normalized?.file_hash },
                ]} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Raw */}
        <TabsContent value="raw">
          <Card><CardContent className="p-4"><CodeBlock code={alert.raw_payload} language={alert.raw_format} /></CardContent></Card>
        </TabsContent>

        {/* Parsed */}
        <TabsContent value="parsed">
          <Card><CardContent className="p-5">
            {alert.normalized ? (
              <KeyValue items={Object.entries(alert.normalized).map(([k, v]) => ({ label: k, value: String(v ?? '—') }))} />
            ) : <EmptyState title="Not parsed yet" />}
            {(alert.entities?.length ?? 0) > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {alert.entities.map((e: any, i: number) => (
                  <Badge key={i} variant="outline">{e.type}: {e.value}</Badge>
                ))}
              </div>
            )}
          </CardContent></Card>
        </TabsContent>

        {/* Enrichment */}
        <TabsContent value="enrichment">
          <Card><CardContent className="p-5">
            {(alert.iocs?.length ?? 0) === 0 ? (
              <EmptyState title="No IOCs enriched yet" description="Run Enrich in the pipeline bar." />
            ) : (
              <div className="space-y-2">
                {alert.iocs.map((i: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{i.ioc_type}</Badge>
                      <span className="font-mono text-sm">{i.value}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">risk {i.risk_score}</span>
                      <Badge variant={i.reputation === 'malicious' ? 'danger' : i.reputation === 'suspicious' ? 'warning' : 'secondary'}>
                        {i.reputation || 'unknown'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent></Card>
        </TabsContent>

        {/* Correlation */}
        <TabsContent value="correlation">
          <Card><CardContent className="p-5">
            {correlation ? (
              correlation.correlation_count === 0 ? <EmptyState title="No correlated alerts" /> : (
                <ul className="space-y-2 text-sm">
                  {correlation.matches.map((m: any, i: number) => (
                    <li key={i} className="flex items-center gap-2">
                      <Badge variant="outline">{m.reason}</Badge>
                      <Link href={`/alerts/${m.alert_id}`} className="text-primary hover:underline">alert #{m.alert_id}</Link>
                      <span className="text-muted-foreground">({m.value})</span>
                    </li>
                  ))}
                </ul>
              )
            ) : <EmptyState title="Run correlation" description="Use the Correlate button above." />}
          </CardContent></Card>
        </TabsContent>

        {/* Investigation */}
        <TabsContent value="investigation">
          {investigation ? (
            <div className="space-y-4">
              <Card><CardHeader><CardTitle>Technical Analysis</CardTitle></CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground">
                  <p>{result.technical_analysis}</p>
                  <p className="text-foreground"><strong>Reasoning:</strong> {result.reasoning_summary}</p>
                </CardContent></Card>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <Card><CardHeader><CardTitle>Evidence</CardTitle></CardHeader>
                  <CardContent><ul className="space-y-1 text-sm">
                    {(result.evidence || []).map((e: any, i: number) => (
                      <li key={i}>• <Badge variant="outline">{e.importance}</Badge> {e.type}: <span className="font-mono">{e.value}</span> <span className="text-muted-foreground">({e.source})</span></li>
                    ))}
                    {(result.evidence || []).length === 0 && <li className="text-muted-foreground">No discrete evidence.</li>}
                  </ul></CardContent></Card>
                <Card><CardHeader><CardTitle>Missing Evidence</CardTitle></CardHeader>
                  <CardContent><ul className="space-y-1 text-sm text-muted-foreground">
                    {(result.missing_evidence || []).map((m: string, i: number) => <li key={i}>• {m}</li>)}
                  </ul></CardContent></Card>
              </div>
              <Card><CardHeader><CardTitle>Recommended Actions</CardTitle></CardHeader>
                <CardContent>
                  <p className="mb-2 text-xs text-amber-400">All response actions are recommendations only and require human approval.</p>
                  <ul className="space-y-2 text-sm">
                    {(result.recommended_actions || []).map((a: any, i: number) => (
                      <li key={i} className="rounded-md border border-border px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Badge variant={a.priority === 'high' ? 'danger' : 'secondary'}>{a.priority}</Badge>
                          {a.requires_human_approval && <Badge variant="outline">human approval</Badge>}
                        </div>
                        <p className="mt-1">{a.action}</p>
                        <p className="text-xs text-muted-foreground">{a.reason}</p>
                      </li>
                    ))}
                  </ul>
                </CardContent></Card>
              {(result.qa_warnings || []).length > 0 && (
                <Card><CardHeader><CardTitle>QA Warnings</CardTitle></CardHeader>
                  <CardContent><ul className="space-y-1 text-sm text-amber-400">
                    {result.qa_warnings.map((w: string, i: number) => <li key={i}>⚠️ {w}</li>)}
                  </ul></CardContent></Card>
              )}
            </div>
          ) : <EmptyState title="No investigation yet" description="Run Investigate above." />}
        </TabsContent>

        {/* MITRE */}
        <TabsContent value="mitre">
          <Card><CardContent className="p-5">
            {(result.mitre_mapping || []).length === 0 ? <EmptyState title="No MITRE mapping" /> : (
              <div className="space-y-2">
                {result.mitre_mapping.map((m: any, i: number) => (
                  <div key={i} className="rounded-md border border-border px-3 py-2">
                    <div className="flex items-center gap-2">
                      <Badge>{m.technique_id}</Badge>
                      <span className="font-medium">{m.technique}</span>
                      <span className="text-xs text-muted-foreground">{m.tactic}</span>
                      {m.confidence != null && <span className="ml-auto text-xs text-muted-foreground">conf {m.confidence}</span>}
                    </div>
                    {m.reason && <p className="mt-1 text-sm text-muted-foreground">{m.reason}</p>}
                  </div>
                ))}
              </div>
            )}
          </CardContent></Card>
        </TabsContent>

        {/* Detection queries */}
        <TabsContent value="detection">
          <div className="space-y-3">
            {[['splunk', 'Splunk SPL'], ['crowdstrike_logscale', 'CrowdStrike LogScale'], ['wazuh', 'Wazuh'], ['elastic_kql', 'Elastic KQL'], ['sigma', 'Sigma'], ['sentinel_kql', 'Microsoft Sentinel KQL']].map(([k, label]) =>
              dq[k] ? (
                <Card key={k}><CardHeader><CardTitle>{label}</CardTitle></CardHeader>
                  <CardContent><CodeBlock code={dq[k]} language={k} /></CardContent></Card>
              ) : null
            )}
            {Object.keys(dq).length === 0 && <EmptyState title="No detection queries" description="Run Investigate to generate queries." />}
          </div>
        </TabsContent>

        {/* Report */}
        <TabsContent value="report">
          <Card><CardContent className="p-5">
            {report ? (
              <>
                <div className="mb-3 flex items-center gap-2">
                  <Link href={`/reports/${report.id}`}><Button size="sm" variant="outline">Open full report</Button></Link>
                  <VerdictBadge verdict={report.verdict} />
                </div>
                <ReportMarkdown id={String(report.id)} />
              </>
            ) : <EmptyState title="No report yet" description="Run Generate Report above." />}
          </CardContent></Card>
        </TabsContent>

        {/* Feedback */}
        <TabsContent value="feedback">
          <Card><CardContent className="space-y-3 p-5">
            {investigation ? (
              <>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div>
                    <Label>Analyst label</Label>
                    <Select value={feedback} onChange={(e) => setFeedback(e.target.value)}>
                      {['TP', 'FP', 'Benign', 'Duplicate', 'Escalated', 'Customer Confirmed'].map((l) => <option key={l}>{l}</option>)}
                    </Select>
                  </div>
                </div>
                <div>
                  <Label>Comment</Label>
                  <Textarea rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
                </div>
                <Button onClick={() => api.submitFeedback(String(investigation.id), { comment, ...( { label: feedback } as any) }).then(() => { setComment(''); qc.invalidateQueries({ queryKey: ['audit'] }); })}>
                  Submit Feedback
                </Button>
              </>
            ) : <EmptyState title="Investigate first" />}
          </CardContent></Card>
        </TabsContent>

        {/* Audit */}
        <TabsContent value="audit">
          <Card><CardContent className="p-5">
            <ul className="space-y-1 text-sm">
              {(auditQ.data || []).filter((l: any) => String(l.target_id) === String(alert.id) || l.target_type === 'alert').slice(0, 30).map((l: any) => (
                <li key={l.id} className="flex items-center gap-2 text-muted-foreground">
                  <Badge variant="outline">{l.action}</Badge>
                  <span>{l.actor_email}</span>
                  <span className="ml-auto text-xs">{formatRelative(l.created_at)}</span>
                </li>
              ))}
            </ul>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

const labels: Record<string, string> = {
  overview: 'Overview', raw: 'Raw Alert', parsed: 'Parsed Fields', enrichment: 'IOC Enrichment',
  correlation: 'Correlation', investigation: 'AI Investigation', mitre: 'MITRE', detection: 'Detection Queries',
  report: 'Report', feedback: 'Feedback', audit: 'Audit Trail',
};

function ReportMarkdown({ id }: { id: string }) {
  const q = useQuery({ queryKey: ['report-md', id], queryFn: () => api.getReportMarkdown(id) });
  if (q.isLoading) return <LoadingState />;
  return <pre className="max-h-[600px] overflow-auto whitespace-pre-wrap rounded-md bg-secondary/40 p-4 text-xs">{q.data}</pre>;
}
