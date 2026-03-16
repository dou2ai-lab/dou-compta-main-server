import { NextRequest, NextResponse } from 'next/server';

/**
 * Proxy POST /api/file/upload to file service (POST /api/v1/receipts/upload).
 * Use this path to avoid conflict with /api/receipts/[receiptId] which can
 * match "upload" as receiptId and only supports GET (causing 404 on POST).
 */
const backendBase =
  process.env.NEXT_PUBLIC_FILE_API_URL || 'http://localhost:8005';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File | null;
    const expenseId = formData.get('expense_id') as string | null;

    if (!file) {
      return NextResponse.json({ detail: 'File is required' }, { status: 400 });
    }

    const targetUrl = new URL('/api/v1/receipts/upload', backendBase);
    if (expenseId) {
      targetUrl.searchParams.set('expense_id', expenseId);
    }

    const forwardForm = new FormData();
    forwardForm.append('file', file);

    let res: Response;
    try {
      res = await fetch(targetUrl.toString(), {
        method: 'POST',
        headers: {
          Authorization: 'Bearer dev_mock_token_local',
        },
        body: forwardForm,
      });
    } catch (fetchError: unknown) {
      const message = fetchError instanceof Error ? fetchError.message : 'Unknown error';
      return NextResponse.json(
        {
          detail: `Failed to connect to file service: ${message}`,
          error: 'CONNECTION_ERROR',
          backend_url: targetUrl.toString(),
        },
        { status: 500 },
      );
    }

    const text = await res.text();
    let data: unknown;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }

    if (!res.ok) {
      return NextResponse.json(
        {
          detail: (data as { detail?: string })?.detail ?? 'Upload failed',
          raw: data,
          backend_status: res.status,
        },
        { status: res.status },
      );
    }

    return NextResponse.json(data, { status: res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Upload proxy failed';
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
