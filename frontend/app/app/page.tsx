'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useMemo } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { DossierView } from '@/components/console/DossierView';
import { EnrichModeToggle } from '@/components/console/EnrichModeToggle';
import { IntakeForm } from '@/components/console/IntakeForm';
import { JobProgress } from '@/components/console/JobProgress';
import { EmptyState } from '@/components/console/EmptyState';
import { useEnrichMode } from '@/hooks/useEnrichMode';
import { useEnrichmentJob } from '@/hooks/useEnrichmentJob';
import { parseTiersFromQuery } from '@/src/lib/tier-utils';

function ConsolePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { mode, setMode, ready } = useEnrichMode();
  const initialTiers = useMemo(() => parseTiersFromQuery(searchParams.get('tiers')), [searchParams]);
  const jobIdParam = searchParams.get('jobId');

  const { job, loading, polling, pollTimedOut, error, submit } = useEnrichmentJob();

  useEffect(() => {
    if (jobIdParam) {
      router.replace(`/app/jobs/${jobIdParam}`);
    }
  }, [jobIdParam, router]);

  const handleSubmit = async (input: Parameters<typeof submit>[0]) => {
    const created = await submit(input, mode);
    if (created) {
      router.push(`/app/jobs/${created.id}`);
    }
  };

  if (!ready) {
    return null;
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Enrichment workspace</h1>
        <p className="text-sm text-muted-foreground">Async default with live polling. Sync for Tier 2–4 quick runs.</p>
      </div>

      <EnrichModeToggle mode={mode} onChange={setMode} />
      <IntakeForm mode={mode} initialTiers={initialTiers} onSubmit={handleSubmit} loading={loading || polling} />

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {job ? (
        <>
          <JobProgress job={job} polling={polling} pollTimedOut={pollTimedOut} />
          <DossierView job={job} />
        </>
      ) : (
        <EmptyState
          title="No active job"
          description="Submit an identifier to run the enrichment pipeline. Results appear here with live updates."
        />
      )}
    </div>
  );
}

export default function ConsolePage() {
  return (
    <Suspense fallback={null}>
      <ConsolePageContent />
    </Suspense>
  );
}
