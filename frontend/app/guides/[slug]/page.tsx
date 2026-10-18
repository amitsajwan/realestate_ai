import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import PostsGrid from '@/components/site/PostsGrid'
import { getMarketingConfig } from '@/lib/marketing/config'
import { articleJsonLd, breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import Link from 'next/link'
import { fetchTopic, say, sayList, topicPath, type Text, type Topic, type TopicTable } from '@/lib/site/topics'

export const revalidate = 60

type Props = { params: Promise<{ slug: string }> }

const STATE: Record<Topic['dates'][number]['state'], Text> = {
  confirmed: { mr: 'निश्चित', hi: 'तय', en: 'confirmed' },
  planned: { mr: 'नियोजित', hi: 'प्रस्तावित', en: 'planned' },
  unconfirmed: { mr: 'निश्चित नाही', hi: 'तय नहीं', en: 'not confirmed' },
}
const UI = {
  checked: { mr: 'शेवटची तपासणी', hi: 'आख़िरी जाँच', en: 'Last checked' },
  dates: { mr: 'महत्त्वाच्या तारखा', hi: 'ज़रूरी तारीखें', en: 'Key dates' },
  updates: { mr: 'आमचे व्हिडिओ अपडेट्स', hi: 'हमारे वीडियो अपडेट', en: 'Our video updates' },
  faq: { mr: 'नेहमी विचारले जाणारे प्रश्न', hi: 'अक्सर पूछे जाने वाले सवाल', en: 'Questions people ask' },
  official: { mr: 'अधिकृत लिंक', hi: 'आधिकारिक लिंक', en: 'Official links' },
  english: { mr: 'Read this in English', hi: 'Read this in English', en: '' },
  sources: { mr: 'स्रोत', hi: 'स्रोत', en: 'Sources' },
} satisfies Record<string, Text>

function day(iso: string | null, lang: string): string {
  const d = iso ? new Date(iso + 'T00:00:00+05:30') : null
  if (!d || Number.isNaN(d.getTime())) return ''
  return new Intl.DateTimeFormat(lang === 'en' ? 'en-IN' : `${lang}-IN`, { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Asia/Kolkata' }).format(d)
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const res = await fetchTopic(slug)
  if (!res.ok) return {}
  const t = res.topic
  // the title carries both languages: people search in Marathi and in English
  return pageMetadata(getMarketingConfig(), { title: t.title.en, description: `${say(t.summary, t.lang)} ${t.summary.en}`.slice(0, 300), path: topicPath(t.slug) })
}

/** A section's facts table; scrolls sideways on a phone instead of squeezing. A row with `href` links its first cell to our page. */
function FactTable({ table, lang }: { table: TopicTable; lang: Topic['lang'] }) {
  return (
    <div className="mt-3">
      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-700">
            <tr>{table.columns.map((c) => <th key={c} scope="col" className="whitespace-nowrap px-3 py-2 font-semibold">{c}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-slate-800">
            {table.rows.map((r, i) => (
              <tr key={i}>
                {r.cells.map((c, j) => (
                  <td key={j} className={`px-3 py-2 ${j === 0 ? 'font-semibold' : ''} ${j > 1 ? 'whitespace-nowrap' : ''}`}>
                    {j === 0 && r.href ? <Link href={r.href} className="text-[#0f2340] underline underline-offset-2">{c}</Link> : c}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {table.note && <p className="mt-2 text-sm text-slate-600">{say(table.note, lang)}</p>}
    </div>
  )
}

/** One language's whole body: status, dates, sections, results, FAQ, links, warning. The page shows its own language; the English
 *  copy sits folded under it (Google reads both). */
function Body({ t, lang }: { t: Topic; lang: Topic['lang'] }) {
  const s = (x: Text | undefined) => say(x, lang)
  return (
    <div lang={lang}>
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
          <ul className="mt-3 list-disc space-y-2 pl-5 text-slate-800">
            {sayList(sec.items, lang).map((x, i) => <li key={i}>{x}</li>)}
          </ul>
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

      {t.faq.length > 0 && (
        <section className="mt-8">
          <h2 className="text-xl font-bold text-[#0f2340]">{s(UI.faq)}</h2>
          <div className="mt-3 space-y-2">
            {t.faq.map((f, i) => (
              <details key={i} className="rounded-xl border border-slate-200 p-3">
                <summary className="cursor-pointer font-semibold text-slate-900">{s(f.q)}</summary>
                <p className="mt-2 text-slate-800">{s(f.a)}</p>
              </details>
            ))}
          </div>
        </section>
      )}

      <section className="mt-8">
        <h2 className="text-xl font-bold text-[#0f2340]">{s(UI.official)}</h2>
        <ul className="mt-3 space-y-1">
          {t.links.map((l) => <li key={l.url}><a href={l.url} rel="nofollow noopener" target="_blank" className="font-semibold text-[#0f2340] underline underline-offset-2">{s(l.label)}</a></li>)}
        </ul>
        <p className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-900">⚠️ {s(t.warning)}</p>
      </section>
    </div>
  )
}

export default async function TopicPage({ params }: Props) {
  const { slug } = await params
  const res = await fetchTopic(slug)
  if (!res.ok && res.notFound) notFound()
  if (!res.ok) {
    return (
      <MarketingShell>
        <p className="mx-auto max-w-3xl px-4 py-14 text-slate-700">This page could not be loaded just now. Please try again in a minute.</p>
      </MarketingShell>
    )
  }
  const t = res.topic
  const cfg = getMarketingConfig()
  const path = topicPath(t.slug)
  const lang = t.lang
  const ld = [
    { ...articleJsonLd(cfg, { title: t.title.en, summary: t.summary.en, path, updated: t.checked_on ?? '' }), inLanguage: lang === 'en' ? 'en-IN' : `${lang}-IN` },
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: t.title.en, path }]),
    {
      '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: t.faq.map((f) => ({ '@type': 'Question', name: say(f.q, lang), acceptedAnswer: { '@type': 'Answer', text: say(f.a, lang) } })),
    },
  ]
  return (
    <MarketingShell>
      <article className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        {ld.map((x, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(x) }} />)}
        <h1 lang={lang} className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{say(t.title, lang)}</h1>
        <p lang={lang} className="mt-3 text-lg text-slate-700">{say(t.summary, lang)}</p>
        {t.checked_on && <p className="mt-2 text-sm text-slate-500">{say(UI.checked, lang)}: {day(t.checked_on, lang)}</p>}

        <div className="mt-6"><Body t={t} lang={lang} /></div>

        {t.updates.length > 0 && (
          <section className="mt-10">
            <h2 lang={lang} className="text-xl font-bold text-[#0f2340]">{say(UI.updates, lang)}</h2>
            <div className="mt-4"><PostsGrid posts={t.updates} /></div>
          </section>
        )}

        {lang !== 'en' && (
          <details className="mt-10 rounded-xl border border-slate-200 p-4">
            <summary className="cursor-pointer font-semibold text-[#0f2340]">{say(UI.english, lang)}</summary>
            <h2 className="mt-4 text-2xl font-bold text-slate-900">{t.title.en}</h2>
            <p className="mt-2 text-slate-700">{t.summary.en}</p>
            <div className="mt-4"><Body t={t} lang="en" /></div>
          </details>
        )}

        {t.sources.length > 0 && (
          <section className="mt-8 text-sm text-slate-600">
            <h2 className="font-semibold">{say(UI.sources, lang)}</h2>
            <ul className="mt-1 list-disc pl-5">
              {t.sources.map((src, i) => (
                <li key={i}>{src.url ? <a href={src.url} rel="nofollow noopener" target="_blank" className="underline underline-offset-2">{src.name}</a> : src.name}{src.read_on ? ` (${src.read_on})` : ''}</li>
              ))}
            </ul>
          </section>
        )}
      </article>
    </MarketingShell>
  )
}
