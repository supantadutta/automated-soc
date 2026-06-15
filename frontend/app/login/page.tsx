'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck } from 'lucide-react';
import { api } from '@/lib/api';
import { setToken } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input, Label } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('admin@autosoc.local');
  const [password, setPassword] = useState('Admin123!');
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [org, setOrg] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res =
        mode === 'login'
          ? await api.login(email, password)
          : await api.register(email, password, undefined, org || undefined);
      setToken(res.access_token);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err?.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-3">
          <div className="rounded-xl bg-primary/15 p-2 text-primary">
            <ShieldCheck className="h-7 w-7" />
          </div>
          <div>
            <h1 className="text-xl font-bold">AutoSOC Command Center</h1>
            <p className="text-xs text-muted-foreground">
              AI-powered SOC automation & investigation
            </p>
          </div>
        </div>
        <Card>
          <CardContent className="p-6">
            <form onSubmit={submit} className="space-y-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@org.com"
                  autoComplete="username"
                />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>
              {mode === 'register' && (
                <div>
                  <Label htmlFor="org">Organization name</Label>
                  <Input
                    id="org"
                    value={org}
                    onChange={(e) => setOrg(e.target.value)}
                    placeholder="Acme MSSP"
                  />
                </div>
              )}
              {error && (
                <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400">
                  {error}
                </p>
              )}
              <Button type="submit" className="w-full" loading={loading}>
                {mode === 'login' ? 'Sign in' : 'Create account'}
              </Button>
            </form>
            <div className="mt-4 text-center text-sm text-muted-foreground">
              {mode === 'login' ? (
                <button className="hover:text-foreground" onClick={() => setMode('register')}>
                  Need an account? Register
                </button>
              ) : (
                <button className="hover:text-foreground" onClick={() => setMode('login')}>
                  Have an account? Sign in
                </button>
              )}
            </div>
            <div className="mt-4 rounded-lg border border-border bg-secondary/40 px-3 py-2 text-center text-xs text-muted-foreground">
              Demo credentials: <span className="text-foreground">admin@autosoc.local</span> /{' '}
              <span className="text-foreground">Admin123!</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
