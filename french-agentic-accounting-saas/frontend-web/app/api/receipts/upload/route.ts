import { NextRequest, NextResponse } from 'next/server';

// Proxy file uploads through Next.js to avoid CORS issues between
// http://localhost:3000 (frontend) and http://localhost:8005 (file-service).
// The browser talks to /api/receipts/upload (same origin), and this route
// forwards the multipart request to the backend file service from the server.

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File | null;
    const expenseId = formData.get('expense_id') as string | null;

    if (!file) {
      return NextResponse.json({ detail: 'File is required' }, { status: 400 });
    }

    const backendBase =
      process.env.NEXT_PUBLIC_FILE_API_URL || 'http://localhost:8005';

    const targetUrl = new URL('/api/v1/receipts/upload', backendBase);
    if (expenseId) {
      targetUrl.searchParams.set('expense_id', expenseId);
    }

    const forwardForm = new FormData();
    forwardForm.append('file', file);

    console.log(`[UPLOAD PROXY] Calling backend: ${targetUrl.toString()}`);
    
    let res: Response;
    try {
      res = await fetch(targetUrl.toString(), {
        method: 'POST',
        headers: {
          // In development, backend accepts any token starting with dev_mock_token
          Authorization: 'Bearer dev_mock_token_local',
        },
        body: forwardForm,
      });
    } catch (fetchError: any) {
      console.error('[UPLOAD PROXY] Fetch error:', fetchError);
      return NextResponse.json(
        { 
          detail: `Failed to connect to backend: ${fetchError.message}`,
          error: 'CONNECTION_ERROR',
          backend_url: targetUrl.toString()
        },
        { status: 500 },
      );
    }

    const text = await res.text();
    console.log(`[UPLOAD PROXY] Backend response status: ${res.status}`);
    console.log(`[UPLOAD PROXY] Backend response body: ${text.substring(0, 500)}`);
    
    let data: any;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }

    if (!res.ok) {
      console.error('[UPLOAD PROXY] Backend error:', data);
      return NextResponse.json(
        { 
          detail: data?.detail ?? 'Upload failed', 
          raw: data,
          backend_status: res.status,
          backend_url: targetUrl.toString()
        },
        { status: res.status },
      );
    }

    return NextResponse.json(data, { status: res.status });
  } catch (err: any) {
    return NextResponse.json(
      { detail: err?.message || 'Upload proxy failed' },
      { status: 500 },
    );
  }
}

