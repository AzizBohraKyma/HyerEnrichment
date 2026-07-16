import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function PrivacyPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Privacy &amp; DSAR</h1>
        <p className="text-sm text-muted-foreground">Internal data subject access request operations.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>DSAR queue</CardTitle>
          <CardDescription>Access and deletion request management will appear here.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Public opt-out is available at /opt-out (no sidebar).</p>
        </CardContent>
      </Card>
    </div>
  );
}
