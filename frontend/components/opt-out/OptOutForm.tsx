'use client';

import { useState } from 'react';
import { submitOptOut } from '@/src/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

export function OptOutForm() {
  const [identifier, setIdentifier] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      await submitOptOut({ identifier: identifier.trim(), reason: reason.trim() || undefined });
      setSubmitted(true);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Submit failed');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Request accepted</CardTitle>
          <CardDescription>We process opt-out requests within 30 days.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Your identifier has been queued for suppression. Future enrichment requests will return an empty dossier.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <p className="text-xs uppercase tracking-widest text-muted-foreground">Data subject request</p>
        <CardTitle>Opt out of enrichment</CardTitle>
        <CardDescription>
          Submit an email, LinkedIn URL, or username to request removal from enrichment processing (LGPD/GDPR).
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="identifier">Identifier</Label>
            <Input
              id="identifier"
              required
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="email, LinkedIn URL, or username"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="reason">Reason (optional)</Label>
            <Textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Optional context for your request"
            />
          </div>
          <Button type="submit" disabled={loading || !identifier.trim()}>
            {loading ? 'Submitting…' : 'Submit opt-out request'}
          </Button>
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
        </form>
      </CardContent>
    </Card>
  );
}
