import React from 'react'
import type { Metadata } from 'next'
import { notFound, permanentRedirect } from 'next/navigation'
import AreaPage from '@/components/area/AreaPage'
import { pageLocality } from '@/components/area/pageLocality'
import { areaPhotoOgImage, getAreaPhotos } from '@/components/localities/areaPhotoData'
import { areaOgImage, readAreaPictures } from '@/components/localities/areaPictures'
import { getMarketingConfig } from '@/lib/marketing/config'
import { LOCALITIES, getLocality, localityNameFromSlug } from '@/lib/marketing/localities'
import { pageMetadata } from '@/lib/marketing/seo'
import { getCatalog, getLocalityListings } from '@/lib/site/api'
import { AREA_GUIDES, areaGuidePath } from '@/lib/site/areaGuide'
import { getRegisterPlaces, placePath } from '@/lib/site/register'

type Props = { params: Promise<{ slug: string }> }

export function generateStaticParams() {
  return LOCALITIES.map((l) => ({ slug: l.slug }))
}

/** The area's first sentence plus what the page has, within a search snippet (160 characters); a long first sentence alone,
 *  cut at a word. */
function areaDescription(summary: string): string {
  const first = summary.split('. ')[0].replace(/\.$/, '')
  const full = `${first}. Who it suits, getting around and what to check before you buy.`
  if (full.length <= 160) return full
  if (first.length <= 159) return first + '.'
  const cut = first.slice(0, 158)
  return cut.slice(0, cut.lastIndexOf(' ')).replace(/[,;:\s]+$/, '') + '…'
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = (await params).slug
  const l = getLocality(slug)
  if (!l) {
    const name = localityNameFromSlug(slug)
    const meta = pageMetadata(getMarketingConfig(), {
      title: `${name}, Pune: live listings and projects`,
      description: `Listings and projects agents have added in ${name}, Pune, with buyer checks before you visit or book.`,
      path: `/localities/${slug}`,
    })
    // no guide of its own: the same stub for every place name an agent typed, so it stays out of search (2026-10-27)
    return { ...meta, robots: { index: false, follow: true } }
  }
  return pageMetadata(getMarketingConfig(), {
    // the guide answers "living in X" and "X review"; "projects in X" belongs to /projects/area/x (docs/plan/seo-system.md
    // section 4 owner map). The old title said "projects" too, so the two pages competed for that search (owner 2026-11-04)
    title: `Living in ${l.name}, Pune: area guide for home buyers`,
    description: areaDescription(l.summary),
    path: `/localities/${l.slug}`,
    // the area from above (Sentinel-2, ours to keep) as its link preview, when the page shows the then-and-now pair; else the
    // first published photo of the place; else the brand's card
    image: areaOgImage(l.name, await readAreaPictures(l.slug)) ?? areaPhotoOgImage(await getAreaPhotos(l.slug)),
  })
}

const validSlug = (slug: string) => /^[a-z0-9]+(?:-[a-z0-9]+){0,8}$/.test(slug)

export default async function LocalityPage({ params }: Props) {
  const slug = (await params).slug
  if (!validSlug(slug)) notFound()
  // an area with its own written guide has one page, the guide, which carries everything this page had (2026-11-23). Naming it
  // canonical was not enough: Google kept this page as its own canonical beside the guide (Search Console, last crawl 2026-11-20),
  // since the two pages said different things. A permanent redirect is an instruction, not a hint.
  if (AREA_GUIDES.has(slug)) permanentRedirect(areaGuidePath(slug))
  const l = pageLocality(slug)
  if (l.fallback) {
    const [listings, projects] = await Promise.all([getLocalityListings(l.listingName), getCatalog(l.listingName)])
    if (listings.length === 0 && projects.length === 0) {
      // no guide and no agent's listing, but MahaRERA projects here (Wanowrie has 50, Magarpatta 16): the place's list is the page
      if ((await getRegisterPlaces()).some((p) => p.slug === slug)) permanentRedirect(placePath(slug))
      notFound()
    }
  }
  // called, not rendered as <AreaPage />: the page awaits it, so the page itself returns the finished tree
  return AreaPage({ l, path: `/localities/${l.slug}` })
}
