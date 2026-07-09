import { NextResponse } from 'next/server';
import { mapBackendHealth } from '@/src/lib/api-adapter';
import { backendFetch } from '@/src/lib/backend-client';

export async function GET() {
  try {
    const backendResponse = await backendFetch('/health');
    if (!backendResponse.ok) {
      return NextResponse.json({ status: 'error', service: 'hyrepath-enrichment' }, { status: 502 });
    }
    const payload = await backendResponse.json();
    return NextResponse.json(mapBackendHealth(payload));
  } catch {
    return NextResponse.json({ status: 'error', service: 'hyrepath-enrichment' }, { status: 502 });
  }
}
