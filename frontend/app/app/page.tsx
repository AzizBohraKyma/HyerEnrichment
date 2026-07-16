import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Pipeline overview and recent enrichment activity.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: 'Jobs today', value: '—' },
          { label: 'Success rate', value: '—' },
          { label: 'Avg. duration', value: '—' },
        ].map((kpi) => (
          <Card key={kpi.label}>
            <CardHeader className="pb-2">
              <CardDescription>{kpi.label}</CardDescription>
              <CardTitle className="text-3xl">{kpi.value}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick actions</CardTitle>
          <CardDescription>Start a new enrichment run or review past jobs.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button asChild>
            <Link href="/app/enrich">New enrichment</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/app/history">View history</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
