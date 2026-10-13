import React from 'react'
import { formatDay } from '@/lib/site/projects'
import type { WebFacts } from '@/lib/site/webfacts'

/** Facts from the builder's site and the property sites that rank for the project, each with where it was read. */
export default function WebFactsBox({ web, name }: { web: WebFacts | null | undefined; name: string }) {
  if (!web || !web.facts.length) return null
  return (
    <section aria-labelledby="web-facts-title">
      <h2 id="web-facts-title" className="text-xl font-bold">What the builder and property sites say about {name}</h2>
      <dl className="mt-3 grid gap-3 sm:grid-cols-2">
        {web.facts.map((f) => (
          <div key={f.key} className="rounded-2xl border border-slate-200 bg-white p-4">
            <dt className="text-sm text-slate-600">{f.label}</dt>
            <dd className="mt-1 text-lg font-bold text-slate-900">{f.text}</dd>
            <dd className="mt-1 text-xs text-slate-600">
              From{' '}
              {f.sources.map((s, i) => (
                <React.Fragment key={s.url}>
                  {i > 0 && ', '}
                  <a href={s.url} target="_blank" rel="noopener nofollow" className="underline underline-offset-2">
                    {s.site}{i === 0 && f.official ? " (the builder's site)" : ''}
                  </a>
                </React.Fragment>
              ))}
            </dd>
          </div>
        ))}
      </dl>
      <p className="mt-2 text-xs text-slate-600">
        Shown only when the builder&apos;s own site says it or two sites agree{web.read_at ? `; read on ${formatDay(web.read_at)}` : ''}.
        Where these differ from MahaRERA, MahaRERA&apos;s record is the one that counts.
      </p>
    </section>
  )
}
