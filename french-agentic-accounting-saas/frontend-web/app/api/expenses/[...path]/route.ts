import { NextRequest, NextResponse } from 'next/server';

/**
 * Proxy all /api/expenses/* requests to the expense service (default localhost:8002).
 * Avoids CORS and ERR_CONNECTION_REFUSED in the browser by using same-origin requests;
 * the Next.js server forwards to the expense backend.
 */
const EXPENSE_BASE = process.env.NEXT_PUBLIC_EXPENSE_API_URL || 'http://localhost:8002';

async function proxy(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  try {
    const { path } = await context.params;
    const pathStr = path?.length ? path.join('/') : '';
    const targetPath = pathStr.startsWith('api/') ? pathStr : `api/v1/expenses/${pathStr}`.replace(/\/+$/, '');
    const url = new URL(targetPath, EXPENSE_BASE);
    req.nextUrl.searchParams.forEach((value, key) => url.searchParams.set(key, value));

    const authHeader = req.headers.get('authorization') || 'Bearer dev_mock_token_local';
    const contentType = req.headers.get('content-type');

    const init: RequestInit = {
      method: req.method,
      headers: {
        Authorization: authHeader,
        ...(contentType ? { 'Content-Type': contentType } : {}),
      },
      cache: 'no-store',
    };

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      try {
        const body = await req.text();
        if (body) init.body = body;
      } catch {
        // no body
      }
    }

    const res = await fetch(url.toString(), init);

    if (res.headers.get('content-type')?.includes('application/json')) {
      const data = await res.json().catch(() => ({}));
      return NextResponse.json(data, { status: res.status });
    }
    const text = await res.text();
    return new NextResponse(text, { status: res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Expense service unavailable';
    return NextResponse.json(
      {
        detail: `${message}. Ensure the expense service is running (e.g. run scripts/start-backend-local.ps1).`,
        error: 'CONNECTION_ERROR',
      },
      { status: 503 }
    );
  }
}

export function GET(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(req, context);
}
export function POST(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(req, context);
}
export function PUT(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(req, context);
}
export function DELETE(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(req, context);
}
export function PATCH(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(req, context);
}
