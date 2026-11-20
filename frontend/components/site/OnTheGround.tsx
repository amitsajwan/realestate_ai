import { longDay } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

/** On the ground: what someone saw at the site, said in their words with who went and when (backend areastats/sitevisits.py,
 *  owner 2026-11-20). Everything else on the page is read from MahaRERA and other sites; this is the part only a visit gives, so
 *  it sits high on the page and is never written by a model. Nothing shows without a visit in the last year. */
export default function OnTheGround({ visit }: { visit: RegisterProject['site_visit'] }) {
  if (!visit?.text) return null
  return (
    <section aria-labelledby="ground-title" className="max-w-4xl rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4 sm:p-5" data-testid="on-the-ground">
      <h2 id="ground-title" className="text-xl font-semibold text-slate-900">On the ground</h2>
      <p className="mt-0.5 text-sm text-slate-600" data-testid="visit-line">
        Visited <time dateTime={visit.visited_on}>{longDay(visit.visited_on)}</time> by {visit.by}
      </p>
      <p className="mt-2 leading-relaxed text-slate-900">{visit.text}</p>
    </section>
  )
}
