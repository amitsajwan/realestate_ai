import { serverApiBase } from '@/lib/site/api'
import { BHK_CHOICES, BUDGET_CHOICES } from '@/lib/site/qualification'

/**
 * No-JavaScript path: the page's forms post here, we call the API on the visitor's behalf and redirect back to the
 * page (303), which shows the confirmation. Nothing personal ever goes in the URL; only a status flag does.
 */
const back = (code: string, q: string) =>
  new Response(null, { status: 303, headers: { Location: `/i/${encodeURIComponent(code)}?${q}` } })

/** A configuration or budget chip (no-JS): saved on the lead, then the next question. Never blocks the visitor: any failure moves on. */
async function answer(request: Request, code: string, step: 'bhk' | 'budget', value: string) {
  const next = step === 'bhk' ? 'budget' : 'details'
  const b = BUDGET_CHOICES.find((c) => c.value === value)
  const bhk = Number(value)
  const body = step === 'bhk' ? (BHK_CHOICES.some((c) => c.value === bhk) ? { bhk } : null)
    : b ? { budget_min_inr: b.min, budget_max_inr: b.max } : null
  if (body) {
    try {
      await fetch(serverApiBase() + '/api/v1/public/interest/' + encodeURIComponent(code) + '/answers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Forwarded-For': request.headers.get('x-forwarded-for') || '' },
        body: JSON.stringify(body),
      })
    } catch { /* the answer is optional */ }
  }
  return back(code, 'done=1&q=' + next)
}

export async function POST(request: Request, ctx: { params: Promise<{ code: string }> }) {
  const { code } = await ctx.params
  const form = await request.formData()
  const s = (k: string) => String(form.get(k) ?? '')
  if (s('step') === 'bhk' || s('step') === 'budget') return answer(request, code, s('step') as 'bhk' | 'budget', s(s('step')))
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
    return back(code, 'done=1&q=details&e=' + (res.status === 422 ? 'phone' : 'consent'))
  } catch {
    return back(code, 'e=down')
  }
}
