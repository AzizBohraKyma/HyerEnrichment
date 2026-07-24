"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { EnrichModeToggle } from "@/components/console/EnrichModeToggle";
import { IntakeForm } from "@/components/console/IntakeForm";
import { EmptyState } from "@/components/console/EmptyState";
import { JobProgress } from "@/components/console/JobProgress";
import { JobQueuePanel } from "@/components/console/JobQueuePanel";
import { useCreateEnrichment, useJobCompletionToasts, useJobQuery } from "@/features/enrich";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { patchDraft, setEnrichMode } from "@/store/slices/intakeSlice";
import { parseTiersFromQuery } from "@/src/lib/tier-utils";
import { formatApiErrorMessage } from "@/src/lib/format-api-error";
import { EnrichmentInput } from "@/src/lib/types";
import { useLocalStorageJobs } from "@/hooks/useLocalStorageJobs";
import { isTerminalStatus } from "@/src/lib/enrich-poll";

function EnrichPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const dispatch = useAppDispatch();
  const draft = useAppSelector((state) => state.intake.draft);
  const mode = useAppSelector((state) => state.intake.enrichMode);
  const initialTiers = useMemo(
    () => parseTiersFromQuery(searchParams.get("tiers")),
    [searchParams],
  );
  const createMutation = useCreateEnrichment();
  const trackJobCompletion = useJobCompletionToasts();
  const { addJob, updateJobStatus } = useLocalStorageJobs();

  const [activeAsyncJob, setActiveAsyncJob] = useState<string | null>(null);
  const { data: activeJob, isFetching: isPolling } = useJobQuery(activeAsyncJob ?? undefined);

  useEffect(() => {
    if (initialTiers.length) {
      dispatch(patchDraft({ requestedTiers: initialTiers }));
    }
  }, [dispatch, initialTiers]);

  // Update job queue when active job status changes
  useEffect(() => {
    if (activeJob && activeAsyncJob) {
      updateJobStatus(activeAsyncJob, activeJob.status);

      // Clear active job when it reaches terminal status
      if (isTerminalStatus(activeJob.status)) {
        // Keep showing for a bit, then clear
        const timer = setTimeout(() => {
          setActiveAsyncJob(null);
        }, 3000);
        return () => clearTimeout(timer);
      }
    }
  }, [activeJob, activeAsyncJob, updateJobStatus]);

  // Show toast notification when error occurs
  useEffect(() => {
    if (createMutation.error) {
      toast.error("Request failed", {
        description: formatApiErrorMessage(createMutation.error),
        duration: 5000,
      });
    }
  }, [createMutation.error]);

  const handleSubmit = async (input: EnrichmentInput) => {
    dispatch(patchDraft(input));
    const created = await createMutation.mutateAsync({ input, mode });

    if (mode === "async") {
      toast.success("Job created", { description: created.id });
      trackJobCompletion(created.id);
      addJob(created.id, created.status);
      setActiveAsyncJob(created.id);
      return;
    }

    // Sync mode: redirect to job detail
    router.push(`/app/jobs/${created.id}`);
  };

  const handleViewResults = () => {
    if (activeAsyncJob) {
      router.push(`/app/jobs/${activeAsyncJob}`);
    }
  };

  const showProgress = mode === "async" && activeJob && activeAsyncJob;
  const showViewResults = showProgress && isTerminalStatus(activeJob.status);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Look someone up</h1>
        <p className="text-sm text-muted-foreground">
          Async jobs show live progress below. Sync jobs redirect to results when complete.
        </p>
      </div>

      <JobQueuePanel />

      <EnrichModeToggle mode={mode} onChange={(next) => dispatch(setEnrichMode(next))} />

      {createMutation.error ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{formatApiErrorMessage(createMutation.error)}</AlertDescription>
        </Alert>
      ) : null}

      {showProgress && (
        <div className="space-y-3">
          <JobProgress job={activeJob} polling={isPolling} />
          {showViewResults && (
            <Button onClick={handleViewResults} className="w-full" size="lg">
              View Full Results
            </Button>
          )}
        </div>
      )}

      <IntakeForm
        mode={mode}
        initialTiers={draft.requestedTiers}
        onSubmit={handleSubmit}
        loading={createMutation.isPending}
      />

      {!showProgress && (
        <EmptyState
          title="Ready to look up"
          description="Async: live progress appears above after submit. Sync: redirects to results immediately."
        />
      )}
    </div>
  );
}

export default function EnrichPage() {
  return (
    <Suspense fallback={null}>
      <EnrichPageContent />
    </Suspense>
  );
}
