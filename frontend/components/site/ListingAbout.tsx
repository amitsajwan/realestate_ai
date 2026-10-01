import React from 'react'
import { t } from '@/lib/app/strings'
import type { PublicAbout } from '@/lib/site/types'

const NEARBY_ICON: Record<string, string> = { school: '🏫', hospital: '🏥', transit: '🚌', office: '🏢', market: '🛒', park: '🌳', other: '📍' }

export function hasAbout(a?: PublicAbout | null): boolean {
  if (!a) return false
  return !!(a.highlights?.length || a.amenities?.length || a.nearby?.length || a.connectivity?.length ||
    a.water || a.power_backup || a.maintenance || a.parking || a.society || a.project_name)
}

/** Project and area section of the public listing page. Renders nothing when the agent added no `about`. */
export default function ListingAbout({ about, listingAmenities = [] }: { about?: PublicAbout | null; listingAmenities?: string[] }) {
  if (!about || !hasAbout(about)) return null
  const have = new Set(listingAmenities.map((a) => a.toLowerCase()))
  const amenities = (about.amenities ?? []).filter((a) => !have.has(a.toLowerCase()))
  const practical = ([
    ['Parking', about.parking], ['Water', about.water], ['Power backup', about.power_backup],
    ['Maintenance', about.maintenance], ['Society', about.society],
  ] as Array<[string, string | null | undefined]>).filter((r): r is [string, string] => !!r[1])
  return (
    <section aria-labelledby="about-title" data-testid="listing-about" className="space-y-4 rounded-2xl bg-slate-50 p-4">
      <h2 id="about-title" className="text-lg font-bold">{about.project_name ? `${t('aboutPublicAbout')}: ${about.project_name}` : t('aboutPublicAbout')}</h2>
      {about.highlights && about.highlights.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-600">{t('aboutPublicHighlights')}</h3>
          <ul className="mt-1 list-none space-y-1 p-0">
            {about.highlights.map((h) => <li key={h} className="flex gap-2"><span aria-hidden className="text-[var(--site-primary)]">✓</span><span>{h}</span></li>)}
          </ul>
        </div>
      )}
      {amenities.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-600">{t('aboutPublicAmenities')}</h3>
          <ul className="mt-1 flex list-none flex-wrap gap-2 p-0">
            {amenities.map((a) => <li key={a} className="rounded-full bg-white px-3 py-1.5 text-sm">{a}</li>)}
          </ul>
        </div>
      )}
      {practical.length > 0 && (
        <dl className="grid grid-cols-2 gap-2">
          {practical.map(([k, v]) => (
            <div key={k} className="rounded-xl bg-white p-3">
              <dt className="text-xs uppercase tracking-wide text-slate-500">{k}</dt>
              <dd className="mt-0.5 text-sm font-semibold text-slate-900">{v}</dd>
            </div>
          ))}
        </dl>
      )}
      {about.nearby && about.nearby.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-600">{t('aboutPublicNearby')}</h3>
          <ul className="mt-1 list-none space-y-1 p-0">
            {about.nearby.map((n) => (
              <li key={`${n.type}-${n.name}`} className="flex items-baseline gap-2">
                <span aria-hidden>{NEARBY_ICON[n.type] ?? '📍'}</span>
                <span>{n.name}{typeof n.minutes === 'number' && <span className="text-slate-500"> · about {n.minutes} min</span>}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {about.connectivity && about.connectivity.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-600">{t('aboutPublicGetting')}</h3>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {about.connectivity.map((c) => <li key={c}>{c}</li>)}
          </ul>
        </div>
      )}
    </section>
  )
}
