import { NextRequest, NextResponse } from 'next/server';

/**
 * Proxy /api/admin/* to the admin service (default localhost:8003).
 * Avoids CORS and connection issues when frontend runs on different host.
 */
const ADMIN_BASE = process.env.NEXT_PUBLIC_ADMIN_API_URL || 'http://localhost:8003';

async function proxy(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  try {
    const { path } = await context.params;
    const pathStr = path?.length ? path.join('/') : '';
    const targetPath = pathStr.startsWith('api/') ? pathStr : `api/v1/admin/${pathStr}`;
    const url = new URL(targetPath, ADMIN_BASE);
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
        if (body) (init as RequestInit & { body?: string }).body = body;
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
    const message = err instanceof Error ? err.message : 'Admin service unavailable';
    return NextResponse.json(
      { detail: `${message}. Ensure the admin service is running.`, error: 'CONNECTION_ERROR' },
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
