import { LOCALITIES } from '@/lib/marketing/localities'
import { getMarketingConfig } from '@/lib/marketing/config'
import { getFacets } from '@/lib/site/facets'
import { getRegisterPlaces, placePath } from '@/lib/site/register'

/** /llms.txt (llmstxt.org): a short map of the site for AI assistants, written from the same lists as the sitemap. It is a hint
 *  some assistants read, not a ranking signal; the pages themselves are what they quote (docs/plan/seo-system.md "AI search"). */
export const revalidate = 3600

const PLACES_LISTED = 40

export async function GET(): Promise<Response> {
  const site = getMarketingConfig().siteUrl
  const [places, facets] = await Promise.all([getRegisterPlaces().catch(() => []), getFacets().catch(() => [])])
  const ours = new Set(LOCALITIES.map((l) => l.slug))
  const listed = [...places].filter((p) => p.indexable > 0)
    .sort((a, b) => Number(!ours.has(a.slug)) - Number(!ours.has(b.slug)) || b.projects - a.projects).slice(0, PLACES_LISTED)
  const lists = facets.filter((f) => f.indexable && ours.has(f.place_slug) && !f.builder && !f.possession)
  const nameOf = new Map(places.map((p) => [p.slug, p.name]))
  const lines = [
    '# Avasetu',
    '',
    '> Avasetu lists every housing project in Pune registered with MahaRERA (the Maharashtra real estate regulator), with the facts '
      + 'from its public register: registration number, the completion (possession) date the builder filed and whether it moved, '
      + 'and how many homes are booked, each with the date it was read. Prices come from the builder\'s own site or two property '
      + 'sites that agree. No builder pays to be listed or ranked.',
    '',
    '## Areas of Pune: projects and flats',
    ...listed.map((p) => `- [New projects and flats in ${p.name}, Pune](${site}${placePath(p.slug)}): ${p.projects} projects on MahaRERA`),
    '',
    '## Lists by area',
    ...lists.map((f) => `- [${f.label} in ${nameOf.get(f.place_slug) ?? f.place_slug}, Pune](${site}${f.path}): ${f.count} projects`),
    '',
    '## Area guides',
    ...LOCALITIES.map((l) => `- [${l.name}, Pune: buyer guide](${site}/localities/${l.slug})`),
    '',
    '## Data',
    `- [Pune MahaRERA tracker](${site}/pune-maharera-tracker): projects registered, completion dates moved and homes booked across Pune`,
    `- [All Pune projects](${site}/projects)`,
    `- [Builders in Pune](${site}/builders)`,
    `- [News](${site}/news)`,
    '',
  ]
  return new Response(lines.join('\n'), { headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'public, max-age=3600' } })
}
