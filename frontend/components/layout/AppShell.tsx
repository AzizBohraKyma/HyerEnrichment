'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';
import { HealthIndicator } from '@/components/console/HealthIndicator';
import { Button } from '@/components/ui/button';
import { cn } from '@/src/lib/utils';

const navItems = [
  { href: '/app', label: 'Enrich' },
  { href: '/app/history', label: 'History' },
];

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-1">
            <Link href="/" className="text-xs uppercase tracking-widest text-muted-foreground">
              Hyrepath Enrichment
            </Link>
            <p className="text-sm text-muted-foreground">Internal ops console</p>
          </div>
          <nav className="flex flex-wrap items-center gap-2">
            {navItems.map((item) => (
              <Button
                key={item.href}
                asChild
                variant={pathname === item.href || pathname.startsWith(`${item.href}/`) ? 'secondary' : 'ghost'}
                size="sm"
              >
                <Link href={item.href}>{item.label}</Link>
              </Button>
            ))}
            <Button asChild variant="ghost" size="sm">
              <Link href="/opt-out">Opt-out</Link>
            </Button>
            <HealthIndicator />
            <Button variant="outline" size="sm" disabled>
              Sign in (coming soon)
            </Button>
          </nav>
        </div>
      </header>
      <main className={cn('mx-auto max-w-6xl px-4 py-8')}>{children}</main>
      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-xs text-muted-foreground">
          <span>Web UI → BFF → FastAPI</span>
          <div className="flex gap-4">
            <Link href="/opt-out" className="hover:text-foreground">
              Opt-out
            </Link>
            <Link href="/" className="hover:text-foreground">
              Marketing hub
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
