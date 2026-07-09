import { NextRequest, NextResponse } from 'next/server';
import { mapBackendJobListToFrontend, parseBackendError } from '@/src/lib/api-adapter';
import { backendFetch } from '@/src/lib/backend-client';

export async function GET(request: NextRequest) {
  const limit = request.nextUrl.searchParams.get('limit') ?? '50';
  const offset = request.nextUrl.searchParams.get('offset') ?? '0';

  let backendResponse: Response;
  try {
    backendResponse = await backendFetch(`/enrich?limit=${limit}&offset=${offset}`);
  } catch {
    return NextResponse.json({ message: 'Unable to reach enrichment backend.' }, { status: 502 });
  }

  if (!backendResponse.ok) {
    const message = await parseBackendError(backendResponse);
    return NextResponse.json({ message }, { status: backendResponse.status });
  }

  const payload = await backendResponse.json();
  return NextResponse.json(mapBackendJobListToFrontend(payload));
}
