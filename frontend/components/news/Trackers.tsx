import React from 'react'
import Link from 'next/link'
import { KIND_LABEL, TRACKER_TEXT, trackerDate, trackerPath, type Tracker, type TrackerLink, type TrackerReport } from '@/lib/news/trackers'

/** Where a project stands: one segment per stage, done ones filled, the current one gold. Only the current stage is named on a phone
 *  (five labels do not fit 360 px); every label shows from `sm` up. Renders nothing for rules and rates, or an unknown stage. */
export function StageBar({ stages, stage, tone = 'light' }: { stages: string[]; stage: number | null; tone?: 'light' | 'dark' }) {
  if (!stages.length || stage === null) return null
  const dark = tone === 'dark'
  return (
    <div data-testid="stage-bar">
      <p className={`text-xs font-semibold ${dark ? 'text-[#f6d58a]' : 'text-[#7a5a10]'} sm:sr-only`}>Stage {stage + 1} of {stages.length}: {stages[stage]}</p>
      <ol className="mt-1.5 flex list-none gap-1 p-0" aria-label={`Stage ${stage + 1} of ${stages.length}: ${stages[stage]}`}>
        {stages.map((s, i) => (
          <li key={s} className="min-w-0 flex-1" aria-current={i === stage ? 'step' : undefined}>
            <span aria-hidden="true" className={`block h-1.5 rounded-full ${i < stage ? (dark ? 'bg-white/70' : 'bg-[#0f2340]') : i === stage ? 'bg-[#f0b440]' : dark ? 'bg-white/20' : 'bg-slate-200'}`} />
            <span className={`mt-1.5 hidden text-[11px] leading-tight sm:block ${i === stage ? (dark ? 'font-bold text-white' : 'font-bold text-[#0f2340]') : dark ? 'text-white/60' : 'text-slate-500'}`}>{s}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}

function Kicker({ t, linkAreas = false }: { t: Tracker; linkAreas?: boolean }) {
  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
      <span className="rounded-full bg-[#0f2340] px-2.5 py-1 font-bold uppercase tracking-wide text-white">Tracker &middot; {KIND_LABEL[t.kind]}</span>
      {t.areas.map((a) => linkAreas
        ? <Link key={a.slug} href={`/localities/${a.slug}`} className="font-semibold uppercase tracking-wide text-slate-700 underline-offset-2 hover:underline">{a.name}</Link>
        : <span key={a.slug} className="font-semibold uppercase tracking-wide text-slate-600">{a.name}</span>)}
      {t.areas.length === 0 && <span className="font-semibold uppercase tracking-wide text-slate-600">{t.kind === 'project' ? 'Pune' : 'All Pune buyers'}</span>}
    </p>
  )
}

/** One tracker on the news page or an area page: name, stage, today's status and how fresh it is. */
export function TrackerCard({ t }: { t: Tracker }) {
  const href = trackerPath(t.slug)
  return (
    <li data-testid="tracker-card" className="relative flex list-none flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-[#0f2340]/40">
      <Kicker t={t} />
      <h3 className="mt-3 text-lg font-bold leading-snug text-[#0f2340]">
        <Link href={href} className="text-[#0f2340] no-underline after:absolute after:inset-0 hover:underline">{t.name}</Link>
      </h3>
      <div className="mt-3"><StageBar stages={t.stages} stage={t.stage} /></div>
      <p className="mt-3 line-clamp-4 text-sm leading-relaxed text-slate-800">{t.status}</p>
      <p className="mt-auto pt-3 text-xs font-medium text-slate-600">
        {TRACKER_TEXT.statusAsOf} <time dateTime={t.status_date}>{trackerDate(t.status_date)}</time>
        {t.report_count > 0 && <> &middot; {TRACKER_TEXT.reports(t.report_count)}</>}
        {t.newer_reports > 0 && <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 font-bold text-amber-900">New report</span>}
      </p>
    </li>
  )
}

export function TrackerGrid({ items }: { items: Tracker[] }) {
  return <ul className="grid list-none gap-4 p-0 sm:grid-cols-2">{items.map((t) => <TrackerCard key={t.slug} t={t} />)}</ul>
}

function Outlink({ l, children }: { l: TrackerLink | TrackerReport; children: React.ReactNode }) {
  return l.url
    ? <a href={l.url} target="_blank" rel="noopener noreferrer nofollow" className="text-[#0f2340] underline-offset-2 hover:underline">{children}</a>
    : <>{children}</>
}

/** The tracker page: where it stands, what it means, the reports and how the status changed. */
export function TrackerPage({ t }: { t: Tracker }) {
  return (
    <article data-testid="tracker-page" className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <p className="text-sm"><Link href="/news" className="text-[#0f2340] underline underline-offset-2">{TRACKER_TEXT.all}</Link></p>
      <div className="mt-4"><Kicker t={t} linkAreas /></div>
      <h1 className="mt-3 text-3xl font-extrabold leading-tight tracking-tight text-[#0f2340] sm:text-4xl">{t.title}</h1>
      {t.summary && <p className="mt-3 text-lg leading-relaxed text-slate-700">{t.summary}</p>}

      <section aria-labelledby="now-h" className="mt-7 rounded-3xl bg-[#0f2340] p-5 text-white sm:p-7">
        <h2 id="now-h" className="text-xs font-bold uppercase tracking-[0.14em] text-[#f6d58a]">Where it stands</h2>
        {t.stage !== null && <div className="mt-3"><StageBar stages={t.stages} stage={t.stage} tone="dark" /></div>}
        <p className="mt-4 text-lg font-semibold leading-relaxed sm:text-xl" data-testid="tracker-status">{t.status}</p>
        <p className="mt-3 text-sm text-white/75">
          {TRACKER_TEXT.statusAsOf} <time dateTime={t.status_date}>{trackerDate(t.status_date)}</time>
          {t.status_sources.length > 0 && <> &middot; {TRACKER_TEXT.sources} {t.status_sources.join(', ')}</>}
        </p>
        {t.newer_reports > 0 && <p className="mt-3 rounded-xl bg-[#f0b440] px-3 py-2 text-sm font-semibold text-[#0f2340]">{TRACKER_TEXT.newer(t.newer_reports)}</p>}
      </section>

      {t.means && (
        <section aria-labelledby="means-h" className="mt-6 rounded-xl border-l-4 border-[#f0b440] bg-[#fbf6ea] p-4">
          <h2 id="means-h" className="text-sm font-bold uppercase tracking-wide text-[#0f2340]">{TRACKER_TEXT.means}</h2>
          <p className="mt-1 leading-relaxed text-slate-800">{t.means}</p>
        </section>
      )}

      {t.timeline.length > 0 && (
        <section aria-labelledby="tl-h" className="mt-10">
          <h2 id="tl-h" className="text-xl font-bold text-[#0f2340]">{TRACKER_TEXT.timeline}</h2>
          <p className="mt-1 text-sm text-slate-600">{TRACKER_TEXT.timelineLead}</p>
          <ol className="mt-5 list-none border-l-2 border-slate-200 p-0" data-testid="tracker-timeline">
            {t.timeline.map((r, i) => (
              <li key={`${r.date}-${i}`} className="relative pb-6 pl-5 last:pb-0">
                <span aria-hidden="true" className={`absolute -left-[7px] top-1.5 h-3 w-3 rounded-full border-2 border-white ${i === 0 ? 'bg-[#f0b440]' : 'bg-slate-400'}`} />
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500"><time dateTime={r.date}>{trackerDate(r.date)}</time></p>
                <p className="mt-1 break-words font-semibold leading-snug text-slate-900"><Outlink l={r}>{r.headline}</Outlink></p>
                <p className="mt-1 break-words text-sm text-slate-600">
                  {r.source}
                  {r.also.length > 0 && <> &middot; {TRACKER_TEXT.also} {r.also.map((a, j) => <React.Fragment key={a.name}>{j > 0 && ', '}<Outlink l={a}>{a.name}</Outlink></React.Fragment>)}</>}
                </p>
              </li>
            ))}
          </ol>
        </section>
      )}

      {t.history.length > 1 && (
        <section aria-labelledby="hist-h" className="mt-10">
          <h2 id="hist-h" className="text-xl font-bold text-[#0f2340]">{TRACKER_TEXT.history}</h2>
          <ul className="mt-4 list-none space-y-3 p-0">
            {t.history.map((h, i) => (
              <li key={`${h.date}-${i}`} className={`rounded-xl border p-4 ${i === 0 ? 'border-[#0f2340]/30 bg-white' : 'border-slate-200 bg-slate-50'}`}>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <time dateTime={h.date}>{trackerDate(h.date)}</time>{h.stage !== null && <> &middot; {t.stages[h.stage]}</>}{i === 0 && <> &middot; current</>}
                </p>
                <p className="mt-1 leading-relaxed text-slate-800">{h.status}</p>
                {h.sources.length > 0 && <p className="mt-1 text-xs text-slate-600">{TRACKER_TEXT.sources} {h.sources.join(', ')}</p>}
              </li>
            ))}
          </ul>
        </section>
      )}

      <aside className="mt-10 rounded-2xl border border-[#ead9ae] bg-[#fbf6ea] p-5" aria-labelledby="how-h">
        <h2 id="how-h" className="text-lg font-bold text-[#0f2340]">{TRACKER_TEXT.how}</h2>
        <p className="mt-1 text-sm leading-relaxed text-slate-800">{TRACKER_TEXT.howLead}</p>
      </aside>
    </article>
  )
}

/** "What is changing near <area>" on an area page; nothing when no tracker touches it. */
export function AreaTrackers({ name, items }: { name: string; items: Tracker[] }) {
  if (!items.length) return null
  return (
    <section className="mt-9" aria-labelledby="area-trackers-title">
      <h2 id="area-trackers-title" className="text-xl font-semibold text-slate-900">{TRACKER_TEXT.areaHeading(name)}</h2>
      <p className="mt-1 text-sm text-slate-600">{TRACKER_TEXT.areaLead}</p>
      <div className="mt-4"><TrackerGrid items={items} /></div>
      <p className="mt-3 text-sm"><Link href="/news" className="font-semibold text-[#0f2340] underline underline-offset-2">{TRACKER_TEXT.all}</Link></p>
    </section>
  )
}
