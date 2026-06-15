'use client';

import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Cpu, Server, CheckCircle2, XCircle, ShieldAlert, ShieldCheck } from 'lucide-react';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, Label } from '@/components/ui/input';
import { LoadingState } from '@/components/ui/states';

const LABELS: Record<string, string> = {
  openai: 'OpenAI', azure_openai: 'Azure OpenAI', anthropic: 'Anthropic Claude', gemini: 'Google Gemini',
  mistral: 'Mistral', cohere: 'Cohere', groq: 'Groq', openrouter: 'OpenRouter',
  generic_openai: 'Generic OpenAI-Compatible', ollama: 'Ollama (local)', lmstudio: 'LM Studio (local)',
  vllm: 'vLLM (local)', mock: 'Mock (demo)',
};
const LOCAL = new Set(['ollama', 'lmstudio', 'vllm', 'generic_openai', 'mock']);

export default function SettingsPage() {
  const qc = useQueryClient();
  const info = useQuery({ queryKey: ['ai-providers-info'], queryFn: () => api.aiProvidersInfo() });
  const config = useQuery({ queryKey: ['ai-config'], queryFn: () => api.getAiConfig() });
  const ollama = useQuery({ queryKey: ['ollama-models'], queryFn: () => api.ollamaModels() });
  const prompts = useQuery({ queryKey: ['prompts'], queryFn: () => api.listPrompts() });

  const [provider, setProvider] = useState('');
  const [mode, setMode] = useState('');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, any>>({});
  const [evals, setEvals] = useState<Record<number, any>>({});

  useEffect(() => {
    if (config.data) {
      setProvider(config.data.default_provider);
      setMode(config.data.routing_mode);
    }
  }, [config.data]);

  if (info.isLoading || config.isLoading) return <LoadingState label="Loading provider settings…" />;
  const d: any = info.data || {};
  const providers: any[] = d.providers || [];
  const policies: string[] = d.routing_policies || [];
  const cloudSelected = !LOCAL.has(provider);

  async function saveConfig() {
    setSaving(true);
    try {
      await api.updateAiConfig({ default_provider: provider, routing_mode: mode });
      await qc.invalidateQueries({ queryKey: ['ai-config'] });
      await qc.invalidateQueries({ queryKey: ['ai-providers-info'] });
    } finally {
      setSaving(false);
    }
  }

  async function test(p: string) {
    setTesting(p);
    try {
      const res = await api.testProvider(p);
      setResults((r) => ({ ...r, [p]: res }));
    } catch (e: any) {
      setResults((r) => ({ ...r, [p]: { ok: false, detail: e?.message } }));
    } finally {
      setTesting(null);
    }
  }

  async function evalPrompt(id: number) {
    const res = await api.testPrompt(id);
    setEvals((e) => ({ ...e, [id]: res }));
  }

  return (
    <div className="space-y-6">
      <SectionTitle title="AI Provider Settings" description="Configure routing and providers. API keys live only in the backend and are never returned here." />

      {/* Runtime routing config */}
      <Card>
        <CardHeader><CardTitle>AI Routing</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <Label>Default provider</Label>
              <Select value={provider} onChange={(e) => setProvider(e.target.value)}>
                {providers.map((p) => <option key={p.provider} value={p.provider}>{LABELS[p.provider] || p.provider}{p.is_local ? ' · local' : ''}</option>)}
              </Select>
            </div>
            <div>
              <Label>Routing policy</Label>
              <Select value={mode} onChange={(e) => setMode(e.target.value)}>
                {(policies.length ? policies : ['auto']).map((m) => <option key={m} value={m}>{m}</option>)}
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={saveConfig} loading={saving}>Save routing config</Button>
            </div>
          </div>
          {cloudSelected ? (
            <div className="flex items-start gap-2 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-300">
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
              <span><strong>Privacy notice:</strong> "{LABELS[provider] || provider}" is a cloud provider — alert data may be sent to an external API. PII is redacted before external calls{d.pii_redaction ? '' : ' (currently disabled — enable AI_ENABLE_PII_REDACTION)'}. For sensitive customers choose a local provider or enable per-customer local-only mode.</span>
            </div>
          ) : (
            <div className="flex items-start gap-2 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
              <span><strong>Private:</strong> "{LABELS[provider] || provider}" runs locally — no alert data leaves your environment.</span>
            </div>
          )}
          <p className="text-xs text-muted-foreground">Fallback chain: {(d.fallback_chain || []).join(' → ')} · config source: {config.data?.source}</p>
        </CardContent>
      </Card>

      {/* Provider cards */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground">Providers</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {providers.map((p) => {
            const res = results[p.provider];
            return (
              <Card key={p.provider}>
                <CardContent className="space-y-3 p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {p.is_local ? <Server className="h-4 w-4 text-emerald-400" /> : <Cpu className="h-4 w-4 text-primary" />}
                      <span className="font-medium">{LABELS[p.provider] || p.provider}</span>
                    </div>
                    {p.is_default && <Badge>default</Badge>}
                  </div>
                  <div className="flex flex-wrap items-center gap-1.5 text-xs">
                    {p.configured ? (
                      <span className="flex items-center gap-1 text-emerald-400"><CheckCircle2 className="h-3.5 w-3.5" /> configured</span>
                    ) : (
                      <span className="flex items-center gap-1 text-muted-foreground"><XCircle className="h-3.5 w-3.5" /> not configured</span>
                    )}
                    <Badge variant={p.privacy_level === 'local' ? 'success' : 'outline'}>{p.privacy_level}</Badge>
                    <Badge variant="secondary">{p.latency_class}</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">Model: <span className="text-foreground">{p.model || '—'}</span></div>
                  <div className="flex flex-wrap gap-1">
                    {p.supports_json && <Badge variant="outline">json</Badge>}
                    {p.supports_tools && <Badge variant="outline">tools</Badge>}
                    {p.supports_vision && <Badge variant="outline">vision</Badge>}
                    {p.max_context_tokens && <Badge variant="outline">{Math.round(p.max_context_tokens / 1000)}k ctx</Badge>}
                  </div>
                  <div className="flex items-center justify-between">
                    <Button size="sm" variant="outline" loading={testing === p.provider} onClick={() => test(p.provider)}>Test connection</Button>
                    {res && <Badge variant={res.ok ? 'success' : 'danger'}>{res.ok ? 'healthy' : 'unavailable'}</Badge>}
                  </div>
                  {res?.detail && <p className="truncate text-[11px] text-muted-foreground" title={res.detail}>{res.detail}</p>}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Local LLM models */}
      <Card>
        <CardHeader><CardTitle>Local LLM (Ollama)</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm">
          {ollama.data?.available ? (
            <>
              <p className="text-emerald-400">Connected at {ollama.data.base_url}. Installed models:</p>
              <div className="flex flex-wrap gap-2">
                {(ollama.data.models || []).map((m: any) => (
                  <button key={m.name} onClick={() => { setProvider('ollama'); setMode('local_only'); }}
                    className="rounded-md border border-border px-2.5 py-1 text-xs hover:border-primary/50">
                    {m.name}
                  </button>
                ))}
                {(ollama.data.models?.length ?? 0) === 0 && <span className="text-muted-foreground">No models pulled. Run <code>ollama pull llama3.1</code>.</span>}
              </div>
            </>
          ) : (
            <p className="text-muted-foreground">Ollama not reachable ({ollama.data?.detail || 'offline'}). Start Ollama and run <code>ollama pull llama3.1</code> to run AI privately.</p>
          )}
          <pre className="rounded-md bg-secondary/40 p-3 text-xs text-foreground">{`DEFAULT_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1`}</pre>
        </CardContent>
      </Card>

      {/* Prompt management */}
      <Card>
        <CardHeader><CardTitle>Prompt Management</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {(prompts.data || []).map((p: any) => (
            <div key={p.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border px-3 py-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="font-medium">{p.prompt_type}</span>
                <Badge variant="outline">v{p.version}</Badge>
                {p.is_active && <Badge variant="success">active</Badge>}
                <span className="text-xs text-muted-foreground">{p.name}</span>
              </div>
              <div className="flex items-center gap-2">
                {evals[p.id] && <Badge variant="secondary">eval {evals[p.id].score}</Badge>}
                <Button size="sm" variant="ghost" onClick={() => evalPrompt(p.id)}>Test</Button>
                {!p.is_active && (
                  <Button size="sm" variant="outline" onClick={() => api.activatePrompt(p.id).then(() => qc.invalidateQueries({ queryKey: ['prompts'] }))}>Activate</Button>
                )}
              </div>
            </div>
          ))}
          {(prompts.data?.length ?? 0) === 0 && <p className="text-sm text-muted-foreground">No prompt templates.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
