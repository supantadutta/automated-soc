'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { SectionTitle } from '@/components/ui/misc';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select, Label } from '@/components/ui/input';
import { QueryBoundary, EmptyState } from '@/components/ui/states';

export default function CustomersPage() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ['customers'], queryFn: () => api.listCustomers() });
  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('');
  const [crit, setCrit] = useState('medium');
  const [open, setOpen] = useState(false);

  async function create() {
    await api.createCustomer({ name, industry, criticality: crit } as any);
    setName(''); setIndustry(''); setOpen(false);
    qc.invalidateQueries({ queryKey: ['customers'] });
  }

  return (
    <div className="space-y-5">
      <SectionTitle title="Customers" description="Multi-tenant MSSP customers"
        action={<Button onClick={() => setOpen((v) => !v)}>{open ? 'Cancel' : 'New Customer'}</Button>} />
      {open && (
        <Card><CardContent className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-4">
          <div><Label>Name</Label><Input value={name} onChange={(e) => setName(e.target.value)} /></div>
          <div><Label>Industry</Label><Input value={industry} onChange={(e) => setIndustry(e.target.value)} /></div>
          <div><Label>Criticality</Label><Select value={crit} onChange={(e) => setCrit(e.target.value)}>
            {['low', 'medium', 'high', 'critical'].map((c) => <option key={c}>{c}</option>)}
          </Select></div>
          <div className="flex items-end"><Button onClick={create} disabled={!name}>Create</Button></div>
        </CardContent></Card>
      )}
      <QueryBoundary isLoading={q.isLoading} isError={q.isError} error={q.error} data={q.data}
        isEmpty={(q.data?.length ?? 0) === 0} onRetry={() => q.refetch()}
        empty={<EmptyState title="No customers yet" description="Seed data adds Globex and Initech." />}>
        {(rows) => (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {rows.map((c: any) => (
              <Link key={c.id} href={`/customers/${c.id}`}>
                <Card className="transition-colors hover:border-primary/50">
                  <CardContent className="space-y-2 p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold">{c.name}</span>
                      <Badge variant={c.criticality === 'critical' ? 'danger' : 'secondary'}>{c.criticality}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{c.industry || 'Industry n/a'}</p>
                    <p className="text-xs text-muted-foreground">{c.contact_email}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </QueryBoundary>
    </div>
  );
}
