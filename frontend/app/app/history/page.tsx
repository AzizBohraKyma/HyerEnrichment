'use client';

import { useCallback, useEffect, useState } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { JobHistoryTable } from '@/components/console/JobHistoryTable';
import { listEnrichmentJobs } from '@/src/lib/api-client';
import { JobListItem } from '@/src/lib/types';

const PAGE_SIZE = 50;

export default function HistoryPage() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async (nextOffset: number, append: boolean) => {
    setLoading(true);
    setError('');
    try {
      const response = await listEnrichmentJobs({ limit: PAGE_SIZE, offset: nextOffset });
      setJobs((current) => (append ? [...current, ...response.jobs] : response.jobs));
      setTotal(response.total);
      setOffset(nextOffset);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to load history');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(0, false);
  }, [load]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Job history</h1>
        <p className="text-sm text-muted-foreground">Paginated list from backend. Requires GET /enrich list endpoint.</p>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <JobHistoryTable
        jobs={jobs}
        total={total}
        limit={PAGE_SIZE}
        offset={offset}
        loading={loading}
        onLoadMore={() => void load(offset + PAGE_SIZE, true)}
      />
    </div>
  );
}
