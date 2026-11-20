import { longDay } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

const numbers = (s: string): string[] => s.match(/\d[\d,.]*/g)?.map((x) => x.replace(/[,.]+$/, '').replace(/,/g, '')) ?? []

/** True when a point's sentence already says every number its label does ("0 of 523 homes booked: None of the 523 units have been
 *  booked"): the label then only repeats it, a pattern that read as machine-written (2026-11-20), so the sentence stands alone. A
 *  label with no number, or one whose number the sentence leaves out, still leads. */
export function labelRepeats(label: string, text: string): boolean {
  const own = numbers(label)
  if (!own.length) return false
  const said = new Set(numbers(text))
  if (/\b(none|no)\b/i.test(text)) said.add('0')   // "None of the 523" says the label's 0
  return own.every((x) => said.has(x))
}

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
      {/* a plain heading and a dated line under it: the registration number is on the hero's badge, and a heading made of a
          date and a number read as a template (2026-11-20) */}
      <h2 id="points-title" className="text-lg font-semibold text-slate-900">What stands out</h2>
      <p className="text-sm text-slate-600" data-testid="points-asof">
        {p.details_read_at ? `As of ${longDay(p.details_read_at)}, from MahaRERA and the sources below.` : 'From MahaRERA and the sources below.'}
      </p>
      <ul className="mt-2 list-none space-y-2 p-0">
        {points.map((x) => (
          <li key={x.label} className="text-lg leading-relaxed text-slate-900">
            {labelRepeats(x.label, x.text) ? x.text : <><strong className="font-semibold">{x.label}:</strong> {x.text}</>}
          </li>
        ))}
      </ul>
      {updated && <p className="mt-2 text-sm text-slate-600" data-testid="updated">Updated {longDay(updated)}</p>}
    </section>
  )
}

type Size = NonNullable<RegisterProject['home_sizes']>[number]

/** A size the page may state: from the builder's site or two sites that agree (rule 9), and with its kind of area, since carpet
 *  and saleable differ by 30-40% and a bare number misleads by that much. One site's size, or one whose kind no site states, stays
 *  on the record only (outside review of Godrej Ivara, 2026-11-20: "875 to 1,250 sq ft, area kind not stated (not yet confirmed)"
 *  under a price sheet giving 890 to 1,234). The backend (pages.view) sends only these from then on. */
export const confirmedSize = (x: Size) => !x.one_site && !!x.kind && !/not stated/i.test(x.kind)

/** Each kind of home's size as the builder's site or two sites state it, always with its kind of area. `help` is who confirms a
 *  size (lib/site/sellerHelp). */
export function HomeSizes({ sizes: all, help }: { sizes?: RegisterProject['home_sizes']; name: string; help?: string | null }) {
  const sizes = (all ?? []).filter(confirmedSize)
  if (!sizes.length) return null
  return (
    <section aria-labelledby="sizes-title" data-testid="home-sizes">
      <h2 id="sizes-title" className="text-xl font-bold">Flat sizes</h2>
      <ul className="mt-3 list-none space-y-1 p-0">
        {sizes.map((x) => (
          <li key={x.bhk} className="text-slate-800">
            <strong className="font-semibold">{x.bhk}:</strong> {x.low === x.high ? `${x.low.toLocaleString('en-IN')} sq ft` : `${x.low.toLocaleString('en-IN')} to ${x.high.toLocaleString('en-IN')} sq ft`}, {x.kind}
          </li>
        ))}
      </ul>
      <p className="mt-2 text-sm text-slate-600" data-testid="sizes-note">
        Your agreement for sale states the final carpet area.
        {help && <> <a href="#enquire" className="font-semibold text-[#0f2340] underline underline-offset-2">{help}</a></>}
      </p>
    </section>
  )
}
