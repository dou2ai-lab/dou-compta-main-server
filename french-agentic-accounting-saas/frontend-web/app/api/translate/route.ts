import { NextRequest, NextResponse } from 'next/server'

const LIBRETRANSLATE_DEFAULT_URL = 'https://libretranslate.com'

/**
 * POST /api/translate
 * Body: { text: string, target: 'fr' | 'en' }
 * Proxies to LibreTranslate. Set LIBRETRANSLATE_API_KEY in .env.local for libretranslate.com.
 */
export async function POST(req: NextRequest) {
  const baseUrl = (process.env.LIBRETRANSLATE_API_URL || LIBRETRANSLATE_DEFAULT_URL).replace(/\/$/, '')
  const apiKey = process.env.LIBRETRANSLATE_API_KEY

  let body: { text?: string; target?: string }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const text = typeof body.text === 'string' ? body.text.trim() : ''
  const target = body.target === 'fr' || body.target === 'en' ? body.target : 'fr'

  if (!text) {
    return NextResponse.json({ error: 'Missing or empty "text"' }, { status: 400 })
  }

  const targetLang = target === 'fr' ? 'fr' : 'en'
  const sourceLang = target === 'fr' ? 'en' : 'fr'

  // LibreTranslate accepts form-urlencoded (FormData) or JSON; form is widely supported
  const form = new URLSearchParams()
  form.set('q', text)
  form.set('source', sourceLang)
  form.set('target', targetLang)
  form.set('format', 'text')
  if (apiKey) form.set('api_key', apiKey) // optional: only for instances that require it

  try {
    const res = await fetch(`${baseUrl}/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    })

    const raw = await res.text()
    let data: any
    try {
      data = raw ? JSON.parse(raw) : {}
    } catch {
      console.error('[translate] Non-JSON response:', raw?.slice(0, 200))
      return NextResponse.json(
        { error: 'Translation API error', detail: 'Invalid response from translation service' },
        { status: 502 }
      )
    }

    if (!res.ok) {
      const message = data?.error || data?.message || res.statusText
      console.error('[translate] API error', res.status, message)
      return NextResponse.json(
        { error: 'Translation API error', detail: message },
        { status: res.status === 429 ? 429 : res.status >= 500 ? 502 : 400 }
      )
    }

    const translatedText = data?.translatedText ?? text
    return NextResponse.json({ translatedText })
  } catch (err: any) {
    console.error('[translate] Request failed', err?.message)
    return NextResponse.json(
      { error: 'Translation request failed', detail: err?.message },
      { status: 502 }
    )
  }
}
