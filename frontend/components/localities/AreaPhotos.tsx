import React from 'react'
import { getMarketingConfig } from '@/lib/marketing/config'
import { jsonLdString } from '@/lib/marketing/seo'
import { MAX_PHOTOS, areaPhotosJsonLd, monthYear, sourceName, type AreaPhoto } from './areaPhotoData'

/**
 * Real photos of the area at the top of its guide (docs/plan/area-pictures.md step 4): our own and free-licensed ones, each
 * with who took it, when, and for a licensed one its licence and source, linked. Never an AI picture or a copied one. Sized
 * and lazy except the first, so the page stays fast. Nothing at all when the area has no published photo.
 */
export default function AreaPhotos({ name, photos, className = '' }: { name: string; photos: AreaPhoto[]; className?: string }) {
  const shown = photos.slice(0, MAX_PHOTOS)
  if (!shown.length) return null
  return (
    <section aria-labelledby="area-photos-title" className={className}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(areaPhotosJsonLd(shown, getMarketingConfig().siteUrl, name)) }} />
      <h2 id="area-photos-title" className="text-xl font-semibold text-slate-900">{name} in photos</h2>
      <ul className="mt-4 grid list-none grid-cols-1 gap-4 p-0 sm:grid-cols-2">
        {shown.map((p, i) => (
          <li key={p.id} className={i === 0 && shown.length > 1 && shown.length % 2 === 1 ? 'sm:col-span-2' : ''}>
            <figure className="m-0">
              <img src={p.small_url} srcSet={`${p.small_url} 640w, ${p.url} 1600w`}
                sizes={i === 0 ? '(min-width: 768px) 720px, 100vw' : '(min-width: 768px) 360px, (min-width: 640px) 50vw, 100vw'}
                width={p.width} height={p.height} alt={p.caption} loading={i === 0 ? 'eager' : 'lazy'} decoding="async"
                className="aspect-[4/3] h-auto w-full rounded-xl bg-slate-100 object-cover" />
              <figcaption className="mt-2 text-sm leading-snug text-slate-700">
                <span>{p.caption}</span>
                <span className="text-slate-500"> · Photo: {p.credit}{monthYear(p.taken_on) ? `, ${monthYear(p.taken_on)}` : ''}</span>
                {p.kind === 'licensed' && p.licence && p.licence_url && p.source_url && (
                  <span className="text-slate-500">
                    {' · '}
                    <a href={p.licence_url} target="_blank" rel="license noopener noreferrer" className="underline underline-offset-2">{p.licence}</a>
                    {', via '}
                    <a href={p.source_url} target="_blank" rel="noopener noreferrer nofollow" className="underline underline-offset-2">{sourceName(p.source_url)}</a>
                  </span>
                )}
              </figcaption>
            </figure>
          </li>
        ))}
      </ul>
    </section>
  )
}
