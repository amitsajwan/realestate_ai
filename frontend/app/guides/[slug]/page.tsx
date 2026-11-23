import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import PostsGrid from '@/components/site/PostsGrid'
import { getMarketingConfig } from '@/lib/marketing/config'
import { articleJsonLd, breadcrumbJsonLd, jsonLdString, pageMetadata } from '@/lib/marketing/seo'
import Link from 'next/link'
import { fetchTopic, say, topicPath } from '@/lib/site/topics'
import { Body, UI, day } from '@/components/guides/TopicBody'
import AreaGrowth from '@/components/localities/AreaGrowth'
import AreaLandmarks, { areaQuestions, getAreaLandmarks } from '@/components/localities/AreaLandmarks'
import AreaPhotos from '@/components/localities/AreaPhotos'
import { getAreaPhotos } from '@/components/localities/areaPhotoData'
import { readAreaPictures } from '@/components/localities/areaPictures'
import { getAreaStats } from '@/components/localities/areaStats'
import { getLocality } from '@/lib/marketing/localities'
import FacetChips from '@/components/site/FacetChips'
import { getFacets, placeChips } from '@/lib/site/facets'
import { placePath } from '@/lib/site/register'

export const revalidate = 60

type Props = { params: Promise<{ slug: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const res = await fetchTopic(slug)
  if (!res.ok) return {}
  const t = res.topic
  // the title carries both languages: people search in Marathi and in English
  return pageMetadata(getMarketingConfig(), { title: t.title.en, description: `${say(t.summary, t.lang)} ${t.summary.en}`.slice(0, 300), path: topicPath(t.slug) })
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
  // a guide about one of our areas (today Upper Kharadi) is the page Google keeps for it: the area guide names it canonical, so
  // the area's photos, landmarks, metro and growth are shown here too, or search would never see them (area-pictures.md)
  const area = getLocality(t.slug)
  const [photos, landmarks, stats, pictures] = area
    ? await Promise.all([getAreaPhotos(area.slug), getAreaLandmarks(area.slug), getAreaStats(area.slug), readAreaPictures(area.slug)])
    : [[], null, null, []]
  // the guide stands for the area in search (its locality page names it canonical), so it links the area's projects the way
  // that page did: the place page owns "projects in X" and was linked from nowhere here, so Google showed the guide for
  // "upper kharadi projects" (Search Console 2026-11-23). Only lists live in search, as on the place page.
  const lists = area ? placeChips({ key: area.slug.replace(/-/g, '_'), slug: area.slug }, await getFacets()) : []
  // its questions are in English, so only an English guide carries them (shown and in the FAQPage data alike)
  const more = area && lang === 'en'
    ? areaQuestions(area.name, landmarks, stats?.registered ?? [], stats?.as_of ?? null, t.faq.map((f) => say(f.q, 'en'))) : []
  const ld = [
    { ...articleJsonLd(cfg, { title: t.title.en, summary: t.summary.en, path, updated: t.checked_on ?? '' }), inLanguage: lang === 'en' ? 'en-IN' : `${lang}-IN` },
    breadcrumbJsonLd(cfg.siteUrl, [{ name: 'Home', path: '/' }, { name: t.title.en, path }]),
    {
      '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: [...t.faq.map((f) => ({ q: say(f.q, lang), a: say(f.a, lang) })), ...more]
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

        {area && <AreaPhotos name={area.name} photos={photos} className="mt-8" />}

        {area && (
          <section className="mt-8" aria-labelledby="area-projects">
            <h2 id="area-projects" className="text-xl font-bold text-[#0f2340]">Projects and flats in {area.name}</h2>
            <p className="mt-2"><Link href={placePath(area.slug)} className="font-semibold text-[#0f2340] underline underline-offset-2">See every project in {area.name}</Link>, with possession dates and homes booked from MahaRERA.</p>
            <FacetChips chips={lists} current={placePath(area.slug)} label={`Lists for ${area.name}`} className="mt-3" />
          </section>
        )}

        <div className="mt-6"><Body t={t} lang={lang} /></div>

        {area && (
          <>
            <AreaLandmarks data={landmarks} />
            <AreaGrowth name={area.name} stats={stats} pictures={pictures} siteUrl={cfg.siteUrl} />
            {more.length > 0 && (
              <section className="mt-9" aria-labelledby="area-questions">
                <h2 id="area-questions" className="text-xl font-bold text-[#0f2340]">More questions about {area.name}</h2>
                <dl className="mt-3 space-y-4">{more.map((f) => (<div key={f.q}><dt className="font-semibold text-slate-900">{f.q}</dt><dd className="mt-1 leading-relaxed text-slate-800">{f.a}</dd></div>))}</dl>
              </section>
            )}
          </>
        )}

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
