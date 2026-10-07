import { serverApiBase } from '@/lib/site/api'

/**
 * No-JavaScript path: the page's forms post here, we call the API on the visitor's behalf and redirect back to the
 * page (303), which shows the confirmation. Nothing personal ever goes in the URL; only a status flag does.
 */
const back = (code: string, q: string) =>
  new Response(null, { status: 303, headers: { Location: `/i/${encodeURIComponent(code)}?${q}` } })

export async function POST(request: Request, ctx: { params: Promise<{ code: string }> }) {
  const { code } = await ctx.params
  const form = await request.formData()
  const s = (k: string) => String(form.get(k) ?? '')
  const details = s('step') === 'details'
  const body = details
    ? { name: s('name'), phone: s('phone'), note: s('note'), consent: s('consent') === 'on', website: s('website') }
    : { website: s('website') }
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/interest/' + encodeURIComponent(code), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Forwarded-For': request.headers.get('x-forwarded-for') || '' },
      body: JSON.stringify(body),
    })
    if (res.ok) return back(code, details ? 'done=2' : 'done=1')
    if (res.status === 429) return back(code, 'done=1&e=limit')
    if (res.status === 404) return back(code, 'e=gone')
    return back(code, 'done=1&e=' + (res.status === 422 ? 'phone' : 'consent'))
  } catch {
    return back(code, 'e=down')
  }
}
