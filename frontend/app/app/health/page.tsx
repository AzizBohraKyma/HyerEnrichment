import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function HealthPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">System health</h1>
        <p className="text-sm text-muted-foreground">BFF and backend connectivity status.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Health checks</CardTitle>
          <CardDescription>Detailed health panel will load here.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild variant="outline" size="sm">
            <Link href="/app">Back to dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
