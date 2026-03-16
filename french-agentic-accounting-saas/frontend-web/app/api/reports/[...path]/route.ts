import { NextRequest, NextResponse } from 'next/server';

/**
 * Proxy all /api/reports/* requests to the report service (default localhost:8009).
 * Avoids CORS and ERR_CONNECTION_REFUSED in browser by using same-origin from
 * the Next.js server, which forwards to the report backend.
 */
const REPORT_BASE = process.env.NEXT_PUBLIC_REPORT_API_URL || 'http://localhost:8009';

async function proxy(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  try {
    const { path } = await context.params;
    const pathStr = path?.length ? path.join('/') : '';
    const targetPath = pathStr.startsWith('api/') ? pathStr : `api/v1/reports/${pathStr}`;
    const url = new URL(targetPath, REPORT_BASE);
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
    if (res.headers.get('content-type')?.includes('text/csv') || res.headers.get('content-type')?.includes('spreadsheet')) {
      const blob = await res.blob();
      return new NextResponse(blob, {
        status: res.status,
        headers: {
          'Content-Type': res.headers.get('content-type') || 'application/octet-stream',
          'Content-Disposition': res.headers.get('content-disposition') || 'attachment',
        },
      });
    }
    const text = await res.text();
    return new NextResponse(text, { status: res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Report service unavailable';
    return NextResponse.json(
      { detail: `${message}. Ensure the report service is running (e.g. docker compose up -d).`, error: 'CONNECTION_ERROR' },
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
