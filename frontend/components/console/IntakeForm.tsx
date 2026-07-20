'use client';

import { useEffect, useMemo, useState } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { useHealth } from '@/hooks/useHealth';
import { tierDescriptions } from '@/src/lib/landing-content';
import {
  ALL_TIERS,
  getTierLabel,
  hasValidTierSelection,
  normalizeTiersForMode,
} from '@/src/lib/tier-utils';
import { formatApiErrorMessage } from '@/src/lib/format-api-error';
import { EnrichmentInput, EnrichMode, RequestedTier } from '@/src/lib/types';

type IntakeFormProps = {
  mode: EnrichMode;
  initialTiers?: EnrichmentInput['requestedTiers'];
  onSubmit: (input: EnrichmentInput) => Promise<void>;
  loading?: boolean;
};

export function IntakeForm({ mode, initialTiers, onSubmit, loading }: IntakeFormProps) {
  const { online } = useHealth();
  const [identifier, setIdentifier] = useState('');
  const [company, setCompany] = useState('');
  const [business, setBusiness] = useState('');
  const [jobSearch, setJobSearch] = useState('');

  const [requestedTiers, setRequestedTiers] = useState<RequestedTier[]>(() =>
    normalizeTiersForMode(initialTiers ?? ['tier2', 'tier3'], mode),
  );
  const [error, setError] = useState('');

  useEffect(() => {
    setRequestedTiers(normalizeTiersForMode(initialTiers ?? ['tier2', 'tier3'], mode));
    // Seed from query/draft tiers only; mode changes are handled below.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally ignore mode here
  }, [initialTiers]);

  useEffect(() => {
    setRequestedTiers((prev) => normalizeTiersForMode(prev, mode));
  }, [mode]);

  const hasIdentifier = useMemo(() => Boolean(identifier.trim()), [identifier]);
  const canSubmit = hasIdentifier && hasValidTierSelection(requestedTiers, mode) && online && !loading;

  const toggleTier = (tier: RequestedTier, checked: boolean) => {
    if (mode === 'sync' && tier === 'tier1') {
      return;
    }

    setRequestedTiers((prev) => {
      if (checked) {
        return normalizeTiersForMode([...prev, tier], mode);
      }
      return prev.filter((t) => t !== tier);
    });
  };

  const parseIdentifier = (raw: string): Pick<EnrichmentInput, 'email' | 'linkedinUrl' | 'username'> => {
    const value = raw.trim();
    const looksLikeEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    const looksLikeLinkedIn = /linkedin\.com/i.test(value);

    if (looksLikeEmail) {
      return { email: value };
    }

    if (looksLikeLinkedIn) {
      const normalized = value.startsWith('http') ? value : `https://${value}`;
      return { linkedinUrl: normalized };
    }

    // Treat everything else as a username (strip leading '@' if present).
    return { username: value.replace(/^@/, '') };
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    try {
      const base: EnrichmentInput = {
        requestedTiers: normalizeTiersForMode(requestedTiers, mode),
      };

      const identifierInput = parseIdentifier(identifier);
      if (identifierInput.email) base.email = identifierInput.email;
      if (identifierInput.linkedinUrl) base.linkedinUrl = identifierInput.linkedinUrl;
      if (identifierInput.username) base.username = identifierInput.username;

      const trimmedCompany = company.trim();
      if (trimmedCompany) base.company = trimmedCompany;

      const trimmedBusiness = business.trim();
      if (trimmedBusiness) base.business = trimmedBusiness;

      const trimmedJobSearch = jobSearch.trim();
      if (trimmedJobSearch) base.jobSearch = trimmedJobSearch;

      await onSubmit(base);
    } catch (submitError) {
      setError(formatApiErrorMessage(submitError));
    }
  };

  return (
    <Card>
      <CardHeader>
        <p className="text-xs uppercase tracking-widest text-muted-foreground">Request intake</p>
        <CardTitle className="text-2xl">Look up a person</CardTitle>
        <CardDescription>Paste one identifier. Choose tiers below; extras live under Advanced.</CardDescription>
      </CardHeader>
      <CardContent>
        {mode === 'sync' ? (
          <Alert className="mb-4">
            <AlertDescription>Tier 1 is disabled in sync mode — browser pipeline excluded.</AlertDescription>
          </Alert>
        ) : null}

        <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="identifier">Identifier</Label>
            <Input
              id="identifier"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="Email, LinkedIn URL, or username"
            />
          </div>

          <fieldset className="flex flex-col gap-3 rounded-lg border p-4">
            <legend className="px-1 text-sm font-medium">Tiers</legend>
            <div className="grid gap-3 sm:grid-cols-2">
              {ALL_TIERS.map((tier) => {
                const disabled = mode === 'sync' && tier === 'tier1';
                const checked = requestedTiers.includes(tier);
                const id = `tier-${tier}`;

                return (
                  <label
                    key={tier}
                    htmlFor={id}
                    className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 ${
                      disabled ? 'cursor-not-allowed opacity-50' : ''
                    }`}
                  >
                    <Checkbox
                      id={id}
                      checked={checked}
                      disabled={disabled}
                      onCheckedChange={(value) => toggleTier(tier, value === true)}
                      className="mt-1"
                    />
                    <div>
                      <span className="block text-sm font-medium">{getTierLabel(tier)}</span>
                      <span className="block text-xs text-muted-foreground">{tierDescriptions[tier]}</span>
                    </div>
                  </label>
                );
              })}
            </div>
          </fieldset>

          <Collapsible defaultOpen={false}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" type="button" className="w-fit px-0">
                Advanced
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-4 flex flex-col gap-6 rounded-lg border bg-card p-4">
                <div className="flex flex-col gap-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="flex flex-col gap-2">
                      <Label htmlFor="company">Company (optional)</Label>
                      <Input id="company" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Acme" />
                    </div>
                    <div className="flex flex-col gap-2">
                      <Label htmlFor="business">Business (optional)</Label>
                      <Input id="business" value={business} onChange={(e) => setBusiness(e.target.value)} placeholder="Coffee roasters near SoMa" />
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <Label htmlFor="jobSearch">Job search (optional)</Label>
                    <Input
                      id="jobSearch"
                      value={jobSearch}
                      onChange={(e) => setJobSearch(e.target.value)}
                      placeholder="Staff Backend Engineer"
                    />
                  </div>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>

          <div className="flex flex-col gap-2">
            <Button type="submit" disabled={!canSubmit}>
              {loading ? 'Looking up…' : 'Look up'}
            </Button>
            {!online ? <p className="text-sm text-destructive">Backend unreachable — submit disabled.</p> : null}
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
