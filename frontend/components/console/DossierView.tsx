'use client';

import { Dossier } from '@/src/lib/types';
import { DossierSummary } from '@/components/console/DossierSummary';
import { RawJsonPanel } from '@/components/console/RawJsonPanel';
import { EmptyState } from '@/components/console/EmptyState';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatPercent, initialsFrom } from '@/src/lib/utils';
import { EnrichmentJob } from '@/src/lib/types';

type DossierViewProps = {
  job: EnrichmentJob;
};

function SectionSkeleton() {
  return (
    <div className="flex flex-col gap-2">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-20 w-full" />
    </div>
  );
}

function EmptyMessage({ message }: { message: string }) {
  return <p className="text-sm text-muted-foreground">{message}</p>;
}

export function DossierView({ job }: DossierViewProps) {
  const { dossier, status } = job;
  const loading = status === 'running' || status === 'queued';
  const suppressed = status === 'suppressed';

  if (suppressed) {
    return (
      <div className="flex flex-col gap-4">
        <EmptyState
          title="Identifier suppressed"
          description="This identifier opted out of enrichment. The dossier is intentionally empty."
        />
        <RawJsonPanel job={job} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <p className="text-xs uppercase tracking-widest text-muted-foreground">Merged dossier</p>
          <DossierSummary dossier={dossier} loading={loading} />
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="identity">
            <TabsList className="mb-4 flex h-auto flex-wrap">
              <TabsTrigger value="identity">Identity</TabsTrigger>
              <TabsTrigger value="handles">Handles</TabsTrigger>
              <TabsTrigger value="emails">Verified emails</TabsTrigger>
              <TabsTrigger value="github">GitHub & coworkers</TabsTrigger>
              <TabsTrigger value="jobs">Jobs & business</TabsTrigger>
              <TabsTrigger value="confidence">Confidence</TabsTrigger>
              <TabsTrigger value="sources">Sources</TabsTrigger>
            </TabsList>

            <TabsContent value="identity" className="flex flex-col gap-4">
              {loading ? <SectionSkeleton /> : null}
              <IdentitySection dossier={dossier} />
            </TabsContent>
            <TabsContent value="handles">
              {loading && !dossier.handles.length ? <SectionSkeleton /> : <HandlesSection dossier={dossier} />}
            </TabsContent>
            <TabsContent value="emails">
              {loading && !dossier.verifiedEmails.length ? <SectionSkeleton /> : <EmailsSection dossier={dossier} />}
            </TabsContent>
            <TabsContent value="github">
              {loading && !dossier.github ? <SectionSkeleton /> : <GithubSection dossier={dossier} />}
            </TabsContent>
            <TabsContent value="jobs">
              {loading && !dossier.jobs.length ? <SectionSkeleton /> : <JobsBusinessSection dossier={dossier} />}
            </TabsContent>
            <TabsContent value="confidence">
              {loading && !dossier.confidence.length ? <SectionSkeleton /> : <ConfidenceSection dossier={dossier} />}
            </TabsContent>
            <TabsContent value="sources">
              {loading && !dossier.sources.length ? <SectionSkeleton /> : <SourcesSection dossier={dossier} />}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      <RawJsonPanel job={job} />
    </div>
  );
}

function IdentitySection({ dossier }: { dossier: Dossier }) {
  const title = dossier.metadata.identifierSummary || 'Subject';
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Photo</CardTitle>
        </CardHeader>
        <CardContent>
          {dossier.photo ? (
            <div className="flex flex-col gap-2 text-sm">
              <div className="flex size-16 items-center justify-center rounded-full bg-muted text-lg font-semibold">
                {initialsFrom(title)}
              </div>
              <a href={dossier.photo.assetUrl} target="_blank" rel="noreferrer" className="text-accent break-all">
                {dossier.photo.assetUrl}
              </a>
              <p className="text-muted-foreground">
                {dossier.photo.source} · {formatPercent(dossier.photo.confidence)}
              </p>
            </div>
          ) : (
            <EmptyMessage message="No LinkedIn photo returned." />
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Emails</CardTitle>
        </CardHeader>
        <CardContent>
          {dossier.emails.length ? (
            <ul className="flex flex-col gap-2 text-sm">
              {dossier.emails.map((email) => (
                <li key={email}>{email}</li>
              ))}
            </ul>
          ) : (
            <EmptyMessage message="No email addresses returned." />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function HandlesSection({ dossier }: { dossier: Dossier }) {
  if (!dossier.handles.length) {
    return <EmptyMessage message="No social handles returned." />;
  }
  return (
    <ul className="flex flex-col gap-2">
      {dossier.handles.map((handle) => (
        <li key={`${handle.platform}-${handle.username}`} className="rounded-lg border p-3 text-sm">
          <div className="font-medium">
            {handle.platform} · {handle.username}
          </div>
          <a href={handle.profileUrl} target="_blank" rel="noreferrer" className="text-accent break-all">
            {handle.profileUrl}
          </a>
          <div className="text-muted-foreground">{formatPercent(handle.confidence)}</div>
        </li>
      ))}
    </ul>
  );
}

function EmailsSection({ dossier }: { dossier: Dossier }) {
  if (!dossier.verifiedEmails.length) {
    return <EmptyMessage message="No verified email intelligence returned." />;
  }
  return (
    <ul className="flex flex-col gap-2">
      {dossier.verifiedEmails.map((email) => (
        <li key={email.value} className="rounded-lg border p-3 text-sm">
          <div className="font-medium">{email.value}</div>
          <div className="text-muted-foreground">
            {email.status} · {email.source} · {formatPercent(email.confidence)}
          </div>
        </li>
      ))}
    </ul>
  );
}

function GithubSection({ dossier }: { dossier: Dossier }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">GitHub</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          {dossier.github?.profile ? (
            <a href={dossier.github.profile} target="_blank" rel="noreferrer" className="text-accent">
              {dossier.github.profile}
            </a>
          ) : (
            <EmptyMessage message="No GitHub profile." />
          )}
          <p className="mt-2 text-muted-foreground">Public commits: {dossier.github?.publicCommits ?? 0}</p>
          {dossier.github?.organizations.length ? (
            <ul className="mt-2 flex flex-col gap-1">
              {dossier.github.organizations.map((org) => (
                <li key={org}>{org}</li>
              ))}
            </ul>
          ) : null}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Coworkers</CardTitle>
        </CardHeader>
        <CardContent>
          {dossier.coworkers.length ? (
            <ul className="flex flex-col gap-1 text-sm">
              {dossier.coworkers.map((coworker) => (
                <li key={coworker}>{coworker}</li>
              ))}
            </ul>
          ) : (
            <EmptyMessage message="No coworkers returned." />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function JobsBusinessSection({ dossier }: { dossier: Dossier }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {dossier.jobs.length ? (
            <ul className="flex flex-col gap-2 text-sm">
              {dossier.jobs.map((job) => (
                <li key={`${job.title}-${job.company}`} className="rounded border p-2">
                  <div className="font-medium">{job.title}</div>
                  <div className="text-muted-foreground">
                    {job.company} · {job.location} · {job.remote ? 'Remote' : 'On-site'} · {job.source}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyMessage message="No job listings returned." />
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Business</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          {dossier.business ? (
            <ul className="flex flex-col gap-1">
              <li>{dossier.business.name}</li>
              <li>{dossier.business.address}</li>
              <li>
                <a href={dossier.business.website} target="_blank" rel="noreferrer" className="text-accent">
                  {dossier.business.website}
                </a>
              </li>
              <li>{dossier.business.phone}</li>
              <li>Rating: {dossier.business.rating}</li>
            </ul>
          ) : (
            <EmptyMessage message="No business profile returned." />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ConfidenceSection({ dossier }: { dossier: Dossier }) {
  if (!dossier.confidence.length) {
    return <EmptyMessage message="No confidence scoring returned." />;
  }
  return (
    <div className="flex flex-col gap-2">
      {dossier.confidence.map((item) => (
        <div key={item.label} className="flex items-start justify-between rounded-lg border p-3 text-sm">
          <div>
            <div className="font-medium">{item.label}</div>
            <p className="text-muted-foreground">{item.evidence.join(' · ')}</p>
          </div>
          <span>{formatPercent(item.score)}</span>
        </div>
      ))}
    </div>
  );
}

function SourcesSection({ dossier }: { dossier: Dossier }) {
  if (!dossier.sources.length) {
    return <EmptyMessage message="No enrichment sources recorded." />;
  }
  return (
    <ul className="flex flex-col gap-1 text-sm">
      {dossier.sources.map((source) => (
        <li key={source} className="rounded border px-3 py-2">
          {source}
        </li>
      ))}
    </ul>
  );
}
