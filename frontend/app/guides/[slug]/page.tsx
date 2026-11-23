import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import PostsGrid from '@/components/site/PostsGrid'
import { getMarketingConfig } from '@/lib/marketing/config'
import { articleJsonLd, breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import { fetchTopic, say, topicPath } from '@/lib/site/topics'
import { Body, UI, day } from '@/components/guides/TopicBody'
import AreaPage from '@/components/area/AreaPage'
import { areaPhotoOgImage, getAreaPhotos } from '@/components/localities/areaPhotoData'
import { areaOgImage, readAreaPictures } from '@/components/localities/areaPictures'
import { getLocality } from '@/lib/marketing/localities'
import { AREA_GUIDES } from '@/lib/site/areaGuide'

export const revalidate = 60

type Props = { params: Promise<{ slug: string }> }

/** The area a guide stands for: one of ours with its guide named in AREA_GUIDES (where /localities/<slug> redirects to it). */
const areaOf = (slug: string) => (AREA_GUIDES.has(slug) ? getLocality(slug) ?? null : null)

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const res = await fetchTopic(slug)
  if (!res.ok) return {}
  const t = res.topic
  // an area's guide is the area's page: its picture from above (or its first photo) is the link preview, as on the other areas
  const area = areaOf(t.slug)
  const image = area ? areaOgImage(area.name, await readAreaPictures(area.slug)) ?? areaPhotoOgImage(await getAreaPhotos(area.slug)) : undefined
  // the title carries both languages: people search in Marathi and in English
  return pageMetadata(getMarketingConfig(), { title: t.title.en, description: `${say(t.summary, t.lang)} ${t.summary.en}`.slice(0, 300), path: topicPath(t.slug), image })
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
  // a guide about one of our areas is that area's one page: the area page, with the guide's text as its Guide section
  const area = areaOf(t.slug)
  if (area) return AreaPage({ l: { ...area, fallback: false }, topic: t, path: topicPath(t.slug) })
  const cfg = getMarketingConfig()
  const path = topicPath(t.slug)
  const lang = t.lang
  const ld = [
    { ...articleJsonLd(cfg, { title: t.title.en, summary: t.summary.en, path, updated: t.checked_on ?? '' }), inLanguage: lang === 'en' ? 'en-IN' : `${lang}-IN` },
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: t.title.en, path }]),
    {
      '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: t.faq.map((f) => ({ q: say(f.q, lang), a: say(f.a, lang) }))
        .map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
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
