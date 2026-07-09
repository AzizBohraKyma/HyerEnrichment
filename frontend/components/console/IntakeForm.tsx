'use client';

import { useEffect, useMemo, useState } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useHealth } from '@/hooks/useHealth';
import { ALL_TIERS, availableTiersForMode, getTierLabel, hasValidTierSelection } from '@/src/lib/tier-utils';
import { EnrichmentInput, EnrichMode, RequestedTier } from '@/src/lib/types';

type IntakeFormProps = {
  mode: EnrichMode;
  initialTiers?: RequestedTier[];
  onSubmit: (input: EnrichmentInput) => Promise<void>;
  loading?: boolean;
};

const emptyInput = (tiers: RequestedTier[]): EnrichmentInput => ({
  email: '',
  linkedinUrl: '',
  username: '',
  company: '',
  business: '',
  jobSearch: '',
  requestedTiers: tiers,
});

export function IntakeForm({ mode, initialTiers, onSubmit, loading }: IntakeFormProps) {
  const { online } = useHealth();
  const allowedTiers = availableTiersForMode(mode);
  const [form, setForm] = useState<EnrichmentInput>(emptyInput(initialTiers?.length ? initialTiers : ALL_TIERS));
  const [error, setError] = useState('');

  useEffect(() => {
    if (initialTiers?.length) {
      setForm((current) => ({ ...current, requestedTiers: initialTiers }));
    }
  }, [initialTiers]);

  useEffect(() => {
    if (mode === 'sync') {
      setForm((current) => ({
        ...current,
        requestedTiers: current.requestedTiers.filter((tier) => tier !== 'tier1'),
      }));
    }
  }, [mode]);

  const hasIdentifier = useMemo(
    () => Boolean(form.email || form.linkedinUrl || form.username || form.company || form.business || form.jobSearch),
    [form],
  );

  const canSubmit = hasIdentifier && hasValidTierSelection(form.requestedTiers, mode) && online && !loading;

  const toggleTier = (tier: RequestedTier) => {
    setForm((current) => ({
      ...current,
      requestedTiers: current.requestedTiers.includes(tier)
        ? current.requestedTiers.filter((value) => value !== tier)
        : [...current.requestedTiers, tier],
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    try {
      await onSubmit(form);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Submit failed');
    }
  };

  return (
    <Card>
      <CardHeader>
        <p className="text-xs uppercase tracking-widest text-muted-foreground">Request intake</p>
        <CardTitle className="text-2xl">Submit identifiers and tiers</CardTitle>
        <CardDescription>At least one identifier and one tier required.</CardDescription>
      </CardHeader>
      <CardContent>
        {mode === 'sync' ? (
          <Alert className="mb-4">
            <AlertDescription>Tier 1 is disabled in sync mode — browser pipeline excluded.</AlertDescription>
          </Alert>
        ) : null}

        <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              ['email', 'Email', 'alex@company.com'],
              ['linkedinUrl', 'LinkedIn URL', 'https://linkedin.com/in/example'],
              ['username', 'Username', 'alexhyrepath'],
              ['company', 'Company', 'Hyrepath'],
              ['business', 'Local business query', 'Coffee roasters near SoMa'],
              ['jobSearch', 'Job search query', 'Staff Backend Engineer'],
            ].map(([key, label, placeholder]) => (
              <div key={key} className="flex flex-col gap-2">
                <Label htmlFor={key}>{label}</Label>
                <Input
                  id={key}
                  value={form[key as keyof EnrichmentInput] as string}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  placeholder={placeholder}
                />
              </div>
            ))}
          </div>

          <fieldset className="flex flex-col gap-3 rounded-lg border p-4">
            <legend className="px-1 text-sm font-medium">Requested tiers</legend>
            <div className="flex flex-wrap gap-3">
              {ALL_TIERS.map((tier) => {
                const disabled = !allowedTiers.includes(tier);
                return (
                  <label
                    key={tier}
                    className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${disabled ? 'opacity-50' : ''}`}
                  >
                    <Checkbox
                      checked={form.requestedTiers.includes(tier)}
                      disabled={disabled}
                      onCheckedChange={() => toggleTier(tier)}
                    />
                    <span>
                      {tier.toUpperCase()} — {getTierLabel(tier)}
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          <div className="flex flex-col gap-2">
            <Button type="submit" disabled={!canSubmit}>
              {loading ? 'Submitting…' : 'Run enrichment'}
            </Button>
            {!online ? <p className="text-sm text-destructive">Backend unreachable — submit disabled.</p> : null}
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
