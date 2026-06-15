'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Trash2 } from 'lucide-react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select, Label } from '@/components/ui/input';
import { Switch } from '@/components/ui/misc';
import { LoadingState } from '@/components/ui/states';

function LabeledSwitch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
      <span className="text-sm">{label}</span>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}

export default function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const cust = useQuery({ queryKey: ['customer', id], queryFn: () => api.getCustomer(id) });
  const policy = useQuery({ queryKey: ['ai-policy', id], queryFn: () => api.getAiPolicy(id) });
  const allow = useQuery({ queryKey: ['allowlists', id], queryFn: () => api.listAllowlists(id) });

  const [p, setP] = useState<any>({});
  useEffect(() => { if (policy.data) setP(policy.data); }, [policy.data]);

  const [type, setType] = useState('ip');
  const [value, setValue] = useState('');
  const [reason, setReason] = useState('');

  if (cust.isLoading) return <LoadingState label="Loading customer…" />;
  const c: any = cust.data || {};

  async function savePolicy() {
    await api.updateAiPolicy(id, {
      external_ai_allowed: p.external_ai_allowed,
      preferred_provider: p.preferred_provider,
      fallback_allowed: p.fallback_allowed,
      redact_pii_before_ai: p.redact_pii_before_ai,
      store_ai_outputs: p.store_ai_outputs,
      local_only_mode: p.local_only_mode,
    } as any);
    qc.invalidateQueries({ queryKey: ['ai-policy', id] });
  }

  async function addAllow() {
    await api.createAllowlist({ customer_id: Number(id), entry_type: type, value, reason } as any);
    setValue(''); setReason('');
    qc.invalidateQueries({ queryKey: ['allowlists', id] });
  }

  return (
    <div className="space-y-5">
      <div>
        <Link href="/customers" className="text-xs text-muted-foreground hover:text-foreground">← Back to customers</Link>
        <h1 className="mt-1 flex items-center gap-2 text-xl font-bold">{c.name} <Badge variant="secondary">{c.criticality}</Badge></h1>
        <p className="text-sm text-muted-foreground">{c.industry} · {c.contact_email}</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Customer AI Policy</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <LabeledSwitch checked={!!p.external_ai_allowed} onChange={(v) => setP({ ...p, external_ai_allowed: v })} label="External AI allowed" />
            <LabeledSwitch checked={!!p.local_only_mode} onChange={(v) => setP({ ...p, local_only_mode: v })} label="Local-only mode (private)" />
            <LabeledSwitch checked={!!p.fallback_allowed} onChange={(v) => setP({ ...p, fallback_allowed: v })} label="Fallback allowed" />
            <LabeledSwitch checked={!!p.redact_pii_before_ai} onChange={(v) => setP({ ...p, redact_pii_before_ai: v })} label="Redact PII before external AI" />
            <LabeledSwitch checked={!!p.store_ai_outputs} onChange={(v) => setP({ ...p, store_ai_outputs: v })} label="Store AI outputs" />
            <div>
              <Label>Preferred provider</Label>
              <Select value={p.preferred_provider || ''} onChange={(e) => setP({ ...p, preferred_provider: e.target.value || null })}>
                <option value="">— Auto —</option>
                {['mock', 'ollama', 'lmstudio', 'vllm', 'openai', 'anthropic', 'gemini', 'groq', 'openrouter'].map((x) => <option key={x}>{x}</option>)}
              </Select>
            </div>
          </div>
          <Button onClick={savePolicy}>Save policy</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Allowlist</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
            <Select value={type} onChange={(e) => setType(e.target.value)}>
              {['ip', 'domain', 'username', 'hostname', 'hash'].map((t) => <option key={t}>{t}</option>)}
            </Select>
            <Input placeholder="value" value={value} onChange={(e) => setValue(e.target.value)} />
            <Input placeholder="reason" value={reason} onChange={(e) => setReason(e.target.value)} />
            <Button onClick={addAllow} disabled={!value}>Add</Button>
          </div>
          <div className="space-y-2">
            {(allow.data || []).map((a: any) => (
              <div key={a.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{a.entry_type}</Badge>
                  <span className="font-mono">{a.value}</span>
                  <span className="text-muted-foreground">{a.reason}</span>
                </div>
                <button onClick={() => api.deleteAllowlist(String(a.id)).then(() => qc.invalidateQueries({ queryKey: ['allowlists', id] }))} className="text-muted-foreground hover:text-red-400">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
            {(allow.data?.length ?? 0) === 0 && <p className="text-sm text-muted-foreground">No allowlist entries.</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
