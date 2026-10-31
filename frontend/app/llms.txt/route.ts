import { LOCALITIES } from '@/lib/marketing/localities'
import { getMarketingConfig } from '@/lib/marketing/config'
import { getCatalog } from '@/lib/site/api'
import { getFacets } from '@/lib/site/facets'
import { formatPrice } from '@/lib/site/format'
import { priceRange } from '@/lib/site/projects'
import { displayName, getRegisterPlaces, getRegisterProjects, placePath, projectSummary } from '@/lib/site/register'

/** /llms.txt (llmstxt.org): a short map of the site for AI assistants, written from the same lists as the sitemap. It is a hint
 *  some assistants read, not a ranking signal; the pages themselves are what they quote (docs/plan/seo-system.md "AI search"). */
export const revalidate = 3600

const PLACES_LISTED = 40
// project pages in our areas: the ones agents sell first, then the register's being built, priced ones and the newest changes first
const PROJECTS_LISTED = 60

export async function GET(): Promise<Response> {
  const site = getMarketingConfig().siteUrl
  const [places, facets, catalog, register] = await Promise.all([getRegisterPlaces().catch(() => []), getFacets().catch(() => []),
    getCatalog().catch(() => []), getRegisterProjects().catch(() => [])])
  const ours = new Set(LOCALITIES.map((l) => l.slug))
  const areaKeys = new Set(LOCALITIES.map((l) => l.key))
  const areaName = new Map(LOCALITIES.map((l) => [l.key, l.name]))
  const sold = catalog.filter((p) => p.agents.length)
  // an agent-listed project's register pages answer 301 to its shared page: listed once, at the shared page
  const soldRegnos = new Set(sold.flatMap((p) => [p.rera_no, ...(p.registrations ?? []).map((r) => r.regno)]))
  const built = register.filter((r) => r.indexable && r.active !== false && !r.sold_out && r.area && areaKeys.has(r.area) && !soldRegnos.has(r.regno))
    .sort((a, b) => Number(!a.price_from) - Number(!b.price_from) || (b.page_updated ?? '').localeCompare(a.page_updated ?? ''))
  const projects = [
    ...sold.map((p) => `- [${p.name}, ${p.locality}, Pune](${site}/projects/${p.slug}): by ${p.builder} · MahaRERA ${p.rera_no}${p.price_min ? ` · from ${priceRange(p)}` : ''}`),
    ...built.map((r) => `- [${displayName(r)}, ${areaName.get(r.area as string)}, Pune](${site}/projects/${r.slug}): `
      + [projectSummary(r), `MahaRERA ${r.regno}`, r.price_from ? `from ${formatPrice(r.price_from)}` : ''].filter(Boolean).join(' · ')),
  ].slice(0, PROJECTS_LISTED)
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
    ...(projects.length ? ['## Projects: MahaRERA number, possession date, homes booked, price', ...projects, ''] : []),
    '## Area guides',
    ...LOCALITIES.map((l) => `- [${l.name}, Pune: buyer guide](${site}/localities/${l.slug})`),
    '',
    '## Data',
    `- [Pune MahaRERA tracker](${site}/pune-maharera-tracker): projects registered, completion dates moved and homes booked across Pune`,
    `- [All Pune projects](${site}/projects)`,
    `- [East Pune home plan](${site}/home-plan): projects near EON IT Park, Magarpatta and the airport, and a free shortlist for a family's office, budget and size`,
    `- [Builders in Pune](${site}/builders)`,
    `- [News](${site}/news)`,
    '',
  ]
  return new Response(lines.join('\n'), { headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'public, max-age=3600' } })
}
