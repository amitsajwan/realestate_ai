import React from 'react'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import { HubList } from '@/components/site/research/HubView'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { getRegisterPlaces } from '@/lib/site/register'
import { getHubs, HUBS_PATH } from '@/lib/site/research'

// /work-hubs: the IT parks and job centres with pages of their own (docs/plan/pune-intelligence.md C). Kept for an hour.
export const revalidate = 3600

export async function generateMetadata(): Promise<Metadata> {
  const hubs = await getHubs()
  const meta = pageMetadata(getMarketingConfig(), {
    title: 'Work Hubs in Pune: IT Parks, Companies and Drive Times',
    description: 'IT parks and job centres in Pune: the companies at each, drive times from each area at 9 am and 6 pm, and the projects being built nearby.',
    path: HUBS_PATH,
  })
  // an empty list is not a page for search
  return hubs.length ? meta : { ...meta, robots: { index: false, follow: true } }
}

export default async function WorkHubsPage() {
  const [hubs, places] = await Promise.all([getHubs(), getRegisterPlaces()])
  return (
    <MarketingShell>
      <HubList hubs={hubs} placeNames={new Map(places.map((p) => [p.slug, p.name]))} siteUrl={getMarketingConfig().siteUrl} />
    </MarketingShell>
  )
}
