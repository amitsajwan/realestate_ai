import React from 'react'
import type { Metadata } from 'next'
import PostsSection from '@/components/site/PostsSection'
import MarketingShell from '@/components/marketing/MarketingShell'
import HomeHero from '@/components/marketing/home/HomeHero'
import HomeNews from '@/components/marketing/home/HomeNews'
import HomeAreas from '@/components/marketing/home/HomeAreas'
import HomeListings, { realListings } from '@/components/marketing/home/HomeListings'
import HomeGuides from '@/components/marketing/home/HomeGuides'
import HomeAgentBand from '@/components/marketing/home/HomeAgentBand'
import { socialLinks } from '@/lib/marketing/social'
import { getMarketingConfig } from '@/lib/marketing/config'
import { INSIGHTS } from '@/lib/marketing/insights'
import { LOCALITIES } from '@/lib/marketing/localities'
import { jsonLdString, organizationJsonLd, pageMetadata } from '@/lib/marketing/seo'
import { HOME } from '@/lib/marketing/strings'
import { fetchNews } from '@/lib/news/data'
import { getLocalityListings } from '@/lib/site/api'

export const revalidate = 60

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: HOME.metaTitle,
  description: HOME.metaDescription,
  path: '/',
  image: { path: '/brand/og-landing.jpg', width: 1200, height: 630, alt: HOME.ogAlt },
})

/** The guide that compares the three localities side by side: shown with the area guides, not repeated under buyer guides. */
const COMPARE_SLUG = 'kharadi-upper-kharadi-wagholi'

/** Home page for buyers: news, area guides, real homes, buyer guides and our latest posts. The agent story is on /for-agents. */
export default async function HomePage() {
  const cfg = getMarketingConfig()
  // Both sources degrade to empty on an outage (news reports it so the section can say so), so the page always renders.
  const [news, ...perArea] = await Promise.all([
    fetchNews(3),
    ...LOCALITIES.map((l) => getLocalityListings(l.listingName)),
  ])
  const homes = realListings(perArea.flat()).slice(0, 6)
  const compare = INSIGHTS.find((i) => i.slug === COMPARE_SLUG)
  const guides = INSIGHTS.filter((i) => i.slug !== COMPARE_SLUG)
  return (
    <MarketingShell>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(organizationJsonLd(cfg, HOME.metaOrgDescription, Object.values(socialLinks()))) }} />
      <HomeHero />
      <HomeNews items={news.items.slice(0, 3)} failed={!news.ok} />
      <HomeAreas compare={compare}>
        {!homes.length && <p data-testid="homes-empty" className="mt-4 text-slate-700">{HOME.homes.empty}</p>}
      </HomeAreas>
      <HomeListings items={homes} />
      <HomeGuides guides={guides} />
      <PostsSection />
      <HomeAgentBand />
    </MarketingShell>
  )
}
