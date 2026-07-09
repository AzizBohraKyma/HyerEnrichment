import { Inter } from 'next/font/google';
import './globals.css';
import type { Metadata } from 'next';
import { ReactNode } from 'react';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Hyrepath Enrichment',
  description: 'Multi-tier enrichment pipeline — console, marketing, and opt-out.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
