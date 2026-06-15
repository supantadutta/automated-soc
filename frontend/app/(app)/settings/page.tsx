'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Cpu, Server, CheckCircle2, XCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { SectionTitle, KeyValue } from '@/components/ui/misc';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingState } from '@/components/ui/states';

const LABELS: Record<string, string> = {
  openai: 'OpenAI', azure_openai: 'Azure OpenAI', anthropic: 'Anthropic Claude', gemini: 'Google Gemini',
  mistral: 'Mistral', cohere: 'Cohere', groq: 'Groq', openrouter: 'OpenRouter',
  generic_openai: 'Generic OpenAI-Compatible', ollama: 'Ollama (local)', lmstudio: 'LM Studio (local)',
  vllm: 'vLLM (local)', mock: 'Mock (demo)',
};

export default function SettingsPage() {
  const info = useQuery({ queryKey: ['ai-providers-info'], queryFn: () => api.aiProvidersInfo() });
  const [testing, setTesting] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, any>>({});

  if (info.isLoading) return <LoadingState label="Loading provider settings…" />;
  const d: any = info.data || {};
  const providers: any[] = d.providers || [];

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

  return (
    <div className="space-y-6">
      <SectionTitle title="AI Provider Settings" description="Configure providers via environment variables. Keys never leave the backend." />

      <Card>
        <CardHeader><CardTitle>Routing Configuration</CardTitle></CardHeader>
        <CardContent>
          <KeyValue items={[
            { label: 'Default Provider', value: <Badge>{d.default_provider}</Badge> },
            { label: 'Default Model', value: d.default_model },
            { label: 'Routing Mode', value: <Badge variant="secondary">{d.routing_mode}</Badge> },
            { label: 'Fallback Chain', value: (d.fallback_chain || []).join(' → ') },
            { label: 'Fallback Enabled', value: d.fallback_enabled ? 'Yes' : 'No' },
            { label: 'PII Redaction', value: d.pii_redaction ? 'Enabled' : 'Disabled' },
            { label: 'Strict JSON Mode', value: d.strict_json ? 'Enabled' : 'Disabled' },
          ]} />
          <p className="mt-4 text-xs text-muted-foreground">
            Routing modes: <code>auto</code>, <code>cost</code>, <code>quality</code>, <code>privacy</code>, <code>speed</code>, <code>soc_critical</code>, <code>offline</code>.
            Change via <code>AI_ROUTING_MODE</code> / <code>DEFAULT_AI_PROVIDER</code> in <code>.env</code>.
          </p>
        </CardContent>
      </Card>

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
                  <div className="flex items-center gap-2 text-xs">
                    {p.configured ? (
                      <span className="flex items-center gap-1 text-emerald-400"><CheckCircle2 className="h-3.5 w-3.5" /> configured</span>
                    ) : (
                      <span className="flex items-center gap-1 text-muted-foreground"><XCircle className="h-3.5 w-3.5" /> not configured</span>
                    )}
                    {p.is_local && <Badge variant="outline">local / private</Badge>}
                  </div>
                  <div className="text-xs text-muted-foreground">Model: <span className="text-foreground">{p.model || '—'}</span></div>
                  <div className="flex items-center justify-between">
                    <Button size="sm" variant="outline" loading={testing === p.provider} onClick={() => test(p.provider)}>
                      Test connection
                    </Button>
                    {res && (
                      <Badge variant={res.ok ? 'success' : 'danger'}>{res.ok ? 'healthy' : 'unavailable'}</Badge>
                    )}
                  </div>
                  {res?.detail && <p className="truncate text-[11px] text-muted-foreground" title={res.detail}>{res.detail}</p>}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Local LLM Setup</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>Run fully private/offline with a local model. No data leaves your environment.</p>
          <pre className="rounded-md bg-secondary/40 p-3 text-xs text-foreground">{`# Ollama
ollama pull llama3.1
# set in .env:
DEFAULT_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# LM Studio / vLLM (OpenAI-compatible)
LMSTUDIO_BASE_URL=http://localhost:1234/v1
VLLM_BASE_URL=http://localhost:8001/v1`}</pre>
          <p>See <code>docs/local-llm-setup.md</code> for full instructions.</p>
        </CardContent>
      </Card>
    </div>
  );
}
