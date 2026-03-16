import { NextRequest, NextResponse } from 'next/server';

/**
 * Proxy GET /api/receipts/[receiptId]/status to file service.
 * Avoids CORS when frontend (localhost:3000) calls file service (localhost:8005).
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ receiptId: string }> }
) {
  try {
    const { receiptId } = await params;
    if (!receiptId) {
      return NextResponse.json({ detail: 'receiptId is required' }, { status: 400 });
    }

    const backendBase = process.env.NEXT_PUBLIC_FILE_API_URL || 'http://localhost:8005';
    const targetUrl = `${backendBase}/api/v1/receipts/${receiptId}/status`;

    const res = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        Authorization: 'Bearer dev_mock_token_local',
      },
      cache: 'no-store',
    });

    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data, { status: res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Failed to fetch receipt status';
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
