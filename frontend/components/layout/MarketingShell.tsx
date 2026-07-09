import Link from 'next/link';
import { ReactNode } from 'react';
import { Button } from '@/components/ui/button';

type MarketingShellProps = {
  children: ReactNode;
};

export function MarketingShell({ children }: MarketingShellProps) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-sm font-semibold tracking-tight">
            Hyrepath Enrichment
          </Link>
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm">
              <Link href="/opt-out">Opt-out</Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/app">Open console</Link>
            </Button>
          </div>
        </div>
      </header>
      <main>{children}</main>
      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-6 text-xs text-muted-foreground">
          <span>Self-hosted enrichment pipeline</span>
          <div className="flex gap-4">
            <Link href="/opt-out" className="hover:text-foreground">
              Opt-out
            </Link>
            <Link href="/app" className="hover:text-foreground">
              Console
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
