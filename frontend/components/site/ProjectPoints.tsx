import { longDay } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

/** What stands out, the points picked from the stored fact sheet, under one dated line. Both kinds of project page open with it. */
export default function ProjectPoints({ p, updated }: { p: Pick<RegisterProject, 'points' | 'regno' | 'details_read_at'>; updated?: string | null }) {
  const points = (p.points ?? []).filter((x) => x.label && x.text)
  if (!points.length) return null
  return (
    <section className="max-w-4xl" aria-labelledby="points-title" data-testid="project-points">
      <h2 id="points-title" className="text-sm font-medium text-slate-600">
        {p.details_read_at ? `As of ${longDay(p.details_read_at)}, from MahaRERA ${p.regno} and the sources on this page` : `From MahaRERA ${p.regno} and the sources on this page`}
      </h2>
      <ul className="mt-2 list-none space-y-2 p-0">
        {points.map((x) => (
          <li key={x.label} className="text-lg leading-relaxed text-slate-900"><strong className="font-semibold">{x.label}:</strong> {x.text}</li>
        ))}
      </ul>
      {updated && <p className="mt-2 text-sm text-slate-600" data-testid="updated">Updated {longDay(updated)}</p>}
    </section>
  )
}

/** Each kind of home's size as sites state it. The kind of area always goes with it: carpet and saleable differ by 30-40%. */
export function HomeSizes({ sizes, name }: { sizes?: RegisterProject['home_sizes']; name: string }) {
  if (!sizes?.length) return null
  return (
    <section aria-labelledby="sizes-title" data-testid="home-sizes">
      <h2 id="sizes-title" className="text-xl font-bold">{name} flat sizes</h2>
      <ul className="mt-3 list-none space-y-1 p-0">
        {sizes.map((x) => (
          <li key={x.bhk} className="text-slate-800">
            <strong className="font-semibold">{x.bhk}:</strong> {x.low === x.high ? `${x.low.toLocaleString('en-IN')} sq ft` : `${x.low.toLocaleString('en-IN')} to ${x.high.toLocaleString('en-IN')} sq ft`}, {x.kind}
          </li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-slate-600">As stated on the builder&apos;s site or by two property sites. Confirm the carpet area with the builder before you book.</p>
    </section>
  )
}
