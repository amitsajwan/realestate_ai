import React from 'react'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import MarketingShell from '@/components/marketing/MarketingShell'
import { HubBody } from '@/components/site/research/HubView'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { getRegisterPlaces } from '@/lib/site/register'
import { getHub, hubPath, type HubPage } from '@/lib/site/research'
import { hubHead, hubIndexable } from '@/lib/site/researchPages'

// /work-hubs/<slug>: one work hub (components/site/research/HubView). Rendered on first visit, then kept for an hour.
export const revalidate = 3600
export const dynamicParams = true
export async function generateStaticParams(): Promise<{ slug: string }[]> {
  return []
}

type Props = { params: Promise<{ slug: string }> }

async function load(params: Props['params']): Promise<{ h: HubPage; placeName: string; linked: Set<string> } | null> {
  const { slug } = await params
  const got = await getHub(slug)
  // an outage is a temporary error page (not kept), never a 404
  if (!got.ok) throw new Error('Work hub research is temporarily unavailable')
  if (!got.data) return null
  const places = await getRegisterPlaces()
  const name = new Map(places.map((p) => [p.slug, p.name]))
  // only places with a page of their own are linked
  const linked = new Set(places.filter((p) => p.indexable > 0).map((p) => p.slug))
  return { h: got.data, placeName: name.get(got.data.place) ?? got.data.place, linked }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const got = await load(params)
  if (!got) return { title: 'Work hub not found', robots: { index: false } }
  const head = hubHead(got.h, got.placeName)
  const meta = pageMetadata(getMarketingConfig(), { title: head.title, description: head.description, path: hubPath(got.h.slug) })
  return hubIndexable(got.h) ? meta : { ...meta, robots: { index: false, follow: true } }
}

export default async function WorkHubPage({ params }: Props) {
  const got = await load(params)
  if (!got) notFound()
  return (
    <MarketingShell>
      <HubBody h={got.h} placeName={got.placeName} placeLinked={got.linked} siteUrl={getMarketingConfig().siteUrl} />
    </MarketingShell>
  )
}
