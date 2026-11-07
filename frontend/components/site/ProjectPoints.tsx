import { longDay } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

/** What stands out, the points picked from the stored fact sheet, under one dated line. Both kinds of project page open with it. */
export default function ProjectPoints({ p, updated }: { p: Pick<RegisterProject, 'points' | 'regno' | 'details_read_at' | 'read'>; updated?: string | null }) {
  const points = (p.points ?? []).filter((x) => x.label && x.text)
  if (!points.length) return null
  return (
    <section className="max-w-4xl" aria-labelledby="points-title" data-testid="project-points">
      {p.read?.text && (
        <div className="mb-4 rounded-2xl bg-slate-50 p-4" data-testid="avasetu-read">
          <p className="text-sm font-semibold text-slate-900">Avasetu&apos;s read <span className="font-normal text-slate-600">(from MahaRERA data{p.read.on ? `, ${longDay(p.read.on)}` : ''})</span></p>
          <p className="mt-1 text-lg leading-relaxed text-slate-900">{p.read.text}</p>
        </div>
      )}
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

/** Each kind of home's size as sites state it. The kind of area always goes with it: carpet and saleable differ by 30-40%. A size
 *  only one site gives stays marked, without sending the reader to that site. `help` is who confirms a size (lib/site/sellerHelp). */
export function HomeSizes({ sizes, name, help }: { sizes?: RegisterProject['home_sizes']; name: string; help?: string | null }) {
  if (!sizes?.length) return null
  return (
    <section aria-labelledby="sizes-title" data-testid="home-sizes">
      <h2 id="sizes-title" className="text-xl font-bold">{name} flat sizes</h2>
      <ul className="mt-3 list-none space-y-1 p-0">
        {sizes.map((x) => (
          <li key={x.bhk} className="text-slate-800">
            <strong className="font-semibold">{x.bhk}:</strong> {x.low === x.high ? `${x.low.toLocaleString('en-IN')} sq ft` : `${x.low.toLocaleString('en-IN')} to ${x.high.toLocaleString('en-IN')} sq ft`}, {x.kind}{x.one_site && <span className="text-xs text-slate-500"> (not yet confirmed)</span>}
          </li>
        ))}
      </ul>
      <p className="mt-2 text-sm text-slate-600" data-testid="sizes-note">
        The final carpet area depends on the tower and floor, and your agreement for sale states it.
        {help && <> <a href="#enquire" className="font-semibold text-[#0f2340] underline underline-offset-2">{help}</a></>}
      </p>
    </section>
  )
}
