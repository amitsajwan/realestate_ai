import React from 'react'
import Link from 'next/link'
import OpenChatButton from '@/components/site/OpenChatButton'
import { say, sayList, type Availability, type Text, type Topic, type TopicTable } from '@/lib/site/topics'

/** A guide's written body (calendar/topics/<slug>.json), moved from app/guides/[slug]/page.tsx so an area's page can show the same
 *  parts in its own sections: the story (status, dates, sections, results), the questions, and the official links. */

export const STATE: Record<Topic['dates'][number]['state'], Text> = {
  confirmed: { mr: 'निश्चित', hi: 'तय', en: 'confirmed' },
  planned: { mr: 'नियोजित', hi: 'प्रस्तावित', en: 'planned' },
  unconfirmed: { mr: 'निश्चित नाही', hi: 'तय नहीं', en: 'not confirmed' },
}
export const UI = {
  checked: { mr: 'शेवटची तपासणी', hi: 'आख़िरी जाँच', en: 'Last checked' },
  dates: { mr: 'महत्त्वाच्या तारखा', hi: 'ज़रूरी तारीखें', en: 'Key dates' },
  updates: { mr: 'आमचे व्हिडिओ अपडेट्स', hi: 'हमारे वीडियो अपडेट', en: 'Our video updates' },
  faq: { mr: 'नेहमी विचारले जाणारे प्रश्न', hi: 'अक्सर पूछे जाने वाले सवाल', en: 'Questions people ask' },
  official: { mr: 'अधिकृत लिंक', hi: 'आधिकारिक लिंक', en: 'Official links' },
  english: { mr: 'Read this in English', hi: 'Read this in English', en: '' },
  sources: { mr: 'स्रोत', hi: 'स्रोत', en: 'Sources' },
} satisfies Record<string, Text>

export function day(iso: string | null, lang: string): string {
  const d = iso ? new Date(iso + 'T00:00:00+05:30') : null
  if (!d || Number.isNaN(d.getTime())) return ''
  return new Intl.DateTimeFormat(lang === 'en' ? 'en-IN' : `${lang}-IN`, { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Asia/Kolkata' }).format(d)
}

/** Availability from the booked share on MahaRERA: a chip after the project name and a tint on the row. */
export const AVAILABILITY: Record<Availability, { label: string; chip: string; row: string }> = {
  resale: { label: 'Resale only', chip: 'bg-slate-200 text-slate-700', row: 'bg-slate-50' },
  limited: { label: 'Limited', chip: 'bg-amber-100 text-amber-900', row: '' },
  open: { label: 'High availability', chip: 'bg-emerald-100 text-emerald-900', row: 'bg-emerald-50/60' },
}

/** An item's "**Lead-in:** rest" with the lead-in in bold; plain text otherwise. */
export function Item({ text }: { text: string }) {
  const m = /^\*\*(.+?)\*\*\s*([\s\S]*)$/.exec(text)
  return m ? <><strong className="text-slate-900">{m[1]}</strong> {m[2]}</> : <>{text}</>
}

/** A section's facts table; scrolls sideways on a phone instead of squeezing. A row with `href` links its first cell to our page;
 *  a row with `tag` gets an availability chip and tint, and the legend sits under the table. */
export function FactTable({ table, lang }: { table: TopicTable; lang: Topic['lang'] }) {
  const tags = (Object.keys(AVAILABILITY) as Availability[]).filter((k) => table.rows.some((r) => r.tag === k))
  return (
    <div className="mt-3">
      {table.title && <h3 className="mb-2 text-base font-semibold text-slate-900">{say(table.title, lang)}</h3>}
      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-700">
            <tr>{table.columns.map((c) => <th key={c} scope="col" className="whitespace-nowrap px-3 py-2 font-semibold">{c}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-slate-800">
            {table.rows.map((r, i) => (
              <tr key={i} data-tag={r.tag} className={r.tag ? AVAILABILITY[r.tag].row : ''}>
                {r.cells.map((c, j) => (
                  <td key={j} className={`px-3 py-2 ${j === 0 ? 'font-semibold' : ''} ${j > 1 ? 'whitespace-nowrap' : ''}`}>
                    {j === 0 && r.href ? <Link href={r.href} className="text-[#0f2340] underline underline-offset-2">{c}</Link> : c}
                    {j === 0 && r.tag && <span className={`ml-2 inline-block whitespace-nowrap rounded px-1.5 py-0.5 text-xs font-medium ${AVAILABILITY[r.tag].chip}`}>{AVAILABILITY[r.tag].label}</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {tags.length > 0 && (
        <p className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600">
          {tags.map((k) => <span key={k}><span className={`rounded px-1.5 py-0.5 font-medium ${AVAILABILITY[k].chip}`}>{AVAILABILITY[k].label}</span> {k === 'resale' ? '95% or more booked' : k === 'open' ? 'under 30% booked' : '30-94% booked'}</span>)}
        </p>
      )}
      {table.note && <p className="mt-2 text-sm text-slate-600">{say(table.note, lang)}</p>}
    </div>
  )
}

/** The story: status line, key dates, the written sections, and results when the topic has them. */
export function TopicStory({ t, lang }: { t: Topic; lang: Topic['lang'] }) {
  const s = (x: Text | undefined) => say(x, lang)
  return (
    <>
      <p className="rounded-xl border border-amber-300 bg-amber-50 p-4 font-semibold text-amber-900">{s(t.status_line)}</p>

      <h2 className="mt-8 text-xl font-bold text-[#0f2340]">{s(UI.dates)}</h2>
      <dl className="mt-3 divide-y divide-slate-200 rounded-xl border border-slate-200">
        {t.dates.map((d, i) => (
          <div key={i} className="flex flex-col gap-1 p-3 sm:flex-row sm:justify-between sm:gap-4">
            <dt className="text-slate-700">{s(d.label)}</dt>
            <dd className="font-semibold text-slate-900 sm:text-right">
              {s(d.value)}
              {d.state !== 'confirmed' && <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-600">{s(STATE[d.state])}</span>}
            </dd>
          </div>
        ))}
      </dl>

      {t.sections.map((sec) => (
        <section key={sec.id} className="mt-8">
          <h2 className="text-xl font-bold text-[#0f2340]">{s(sec.heading)}</h2>
          {sec.text && <p className="mt-3 text-slate-800">{s(sec.text)}</p>}
          {sec.table && <FactTable table={sec.table} lang={lang} />}
          {sec.tables?.map((tb, i) => <div key={i} className="mt-5"><FactTable table={tb} lang={lang} /></div>)}
          <ul className="mt-3 list-disc space-y-2 pl-5 text-slate-800">
            {sayList(sec.items, lang).map((x, i) => <li key={i}><Item text={x} /></li>)}
          </ul>
          {sec.cta && (
            <div className="mt-5 flex flex-col gap-3 rounded-xl border border-[#0f2340]/20 bg-[#0f2340] p-4 text-white sm:flex-row sm:items-center sm:justify-between">
              <p className="font-semibold">{s(sec.cta.text)}</p>
              <OpenChatButton message={s(sec.cta.message)} label={s(sec.cta.button)}
                className="min-h-[44px] shrink-0 rounded-lg bg-[#f0b440] px-4 font-bold text-slate-900" />
            </div>
          )}
        </section>
      ))}

      {t.results && (
        <section className="mt-8 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <h2 className="text-xl font-bold text-[#0f2340]">{s(t.results.heading)}</h2>
          <p className="mt-2 text-slate-800">{s(t.results.text)}</p>
          {t.results.links.length > 0 && (
            <ul className="mt-3 space-y-1">
              {t.results.links.map((l) => <li key={l.url}><a href={l.url} rel="nofollow noopener" target="_blank" className="font-semibold text-[#0f2340] underline underline-offset-2">{s(l.label)}</a></li>)}
            </ul>
          )}
        </section>
      )}
    </>
  )
}

/** The topic's own questions, each folded under its question. */
export function TopicFaq({ t, lang }: { t: Topic; lang: Topic['lang'] }) {
  if (t.faq.length === 0) return null
  return (
    <section className="mt-8">
      <h2 className="text-xl font-bold text-[#0f2340]">{say(UI.faq, lang)}</h2>
      <div className="mt-3 space-y-2">
        {t.faq.map((f, i) => (
          <details key={i} className="rounded-xl border border-slate-200 p-3">
            <summary className="cursor-pointer font-semibold text-slate-900">{say(f.q, lang)}</summary>
            <p className="mt-2 text-slate-800">{say(f.a, lang)}</p>
          </details>
        ))}
      </div>
    </section>
  )
}

/** The official links and the warning that closes every guide. */
export function TopicLinks({ t, lang }: { t: Topic; lang: Topic['lang'] }) {
  return (
    <section className="mt-8">
      <h2 className="text-xl font-bold text-[#0f2340]">{say(UI.official, lang)}</h2>
      <ul className="mt-3 space-y-1">
        {t.links.map((l) => <li key={l.url}><a href={l.url} rel="nofollow noopener" target="_blank" className="font-semibold text-[#0f2340] underline underline-offset-2">{say(l.label, lang)}</a></li>)}
      </ul>
      <p className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-900">⚠️ {say(t.warning, lang)}</p>
    </section>
  )
}

/** One language's whole body: status, dates, sections, results, FAQ, links, warning. The page shows its own language; the English
 *  copy sits folded under it (Google reads both). */
export function Body({ t, lang }: { t: Topic; lang: Topic['lang'] }) {
  return (
    <div lang={lang}>
      <TopicStory t={t} lang={lang} />
      <TopicFaq t={t} lang={lang} />
      <TopicLinks t={t} lang={lang} />
    </div>
  )
}
