'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input, Label, Select, Textarea } from '@/components/ui/input';

const SAMPLE = `{"alert_name":"C2 Beacon to Known Bad Domain","source_tool":"Suricata","severity":"Critical","src_ip":"10.20.8.55","dest_ip":"203.0.113.66","domain":"beacon.evil-c2.example","detail":"Periodic beaconing to known command-and-control domain"}`;

export default function SubmitAlertPage() {
  const router = useRouter();
  const customers = useQuery({ queryKey: ['customers'], queryFn: () => api.listCustomers() });

  const [title, setTitle] = useState('');
  const [sourceTool, setSourceTool] = useState('');
  const [severity, setSeverity] = useState('Medium');
  const [customerId, setCustomerId] = useState('');
  const [raw, setRaw] = useState('');
  const [autoRun, setAutoRun] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      const alert: any = await api.submitAlert({
        title: title || undefined,
        raw_payload: raw,
        source_tool: sourceTool || undefined,
        severity,
        customer_id: customerId ? Number(customerId) : undefined,
      });
      if (autoRun) {
        await api.parseAlert(alert.id);
        await api.enrichAlert(alert.id);
        await api.investigateAlert(alert.id);
        await api.generateReport(alert.id);
      }
      router.push(`/alerts/${alert.id}`);
    } catch (e: any) {
      setError(e?.message || 'Submission failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <SectionTitle title="Submit Alert" description="Paste raw text or JSON from any SIEM/EDR/WAF" />
      <Card>
        <CardContent className="space-y-4 p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <Label>Title (optional)</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Auto-derived from JSON if blank" />
            </div>
            <div>
              <Label>Source tool</Label>
              <Input value={sourceTool} onChange={(e) => setSourceTool(e.target.value)} placeholder="CrowdStrike, Splunk, Wazuh…" />
            </div>
            <div>
              <Label>Severity</Label>
              <Select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                {['Informational', 'Low', 'Medium', 'High', 'Critical'].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Customer</Label>
              <Select value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
                <option value="">— None —</option>
                {(customers.data || []).map((c: any) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </Select>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between">
              <Label>Raw alert (text or JSON)</Label>
              <button className="text-xs text-primary hover:underline" onClick={() => setRaw(SAMPLE)}>
                Load sample
              </button>
            </div>
            <Textarea
              rows={10}
              value={raw}
              onChange={(e) => setRaw(e.target.value)}
              placeholder="Paste alert payload…"
              className="font-mono text-xs"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input type="checkbox" checked={autoRun} onChange={(e) => setAutoRun(e.target.checked)} />
            Auto-run full pipeline (parse → enrich → investigate → report)
          </label>
          {error && <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</p>}
          <div className="flex justify-end">
            <Button onClick={submit} loading={busy} disabled={!raw.trim()}>
              {autoRun ? 'Submit & Investigate' : 'Submit Alert'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
