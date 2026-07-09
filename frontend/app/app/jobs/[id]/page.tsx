'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { DossierView } from '@/components/console/DossierView';
import { JobProgress } from '@/components/console/JobProgress';
import { EmptyState } from '@/components/console/EmptyState';
import { useEnrichmentJob } from '@/hooks/useEnrichmentJob';

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;
  const { job, loading, polling, pollTimedOut, error, loadJob, startPolling } = useEnrichmentJob();

  useEffect(() => {
    if (!jobId) return;
    void (async () => {
      const loaded = await loadJob(jobId);
      if (loaded && (loaded.status === 'queued' || loaded.status === 'running')) {
        await startPolling(jobId);
      }
    })();
  }, [jobId, loadJob, startPolling]);

  if (loading && !job) {
    return <EmptyState title="Loading job…" description={`Fetching ${jobId}`} />;
  }

  if (error && !job) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!job) {
    return <EmptyState title="Job not found" description={`No job with id ${jobId}`} />;
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Job detail</h1>
        <p className="text-sm text-muted-foreground">Shareable URL with refresh-safe polling.</p>
      </div>
      <JobProgress job={job} polling={polling} pollTimedOut={pollTimedOut} />
      <DossierView job={job} />
    </div>
  );
}
