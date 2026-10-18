import { sitemapGroups, urlsetXml } from '@/lib/site/sitemap'

export const dynamic = 'force-dynamic'

const NAME = /^([a-z0-9]+(?:-[a-z0-9]+)*)\.xml$/

/** One sitemap of the index (/sitemap.xml): /sitemaps/core.xml, /sitemaps/area-kharadi.xml, ... */
export async function GET(_req: Request, { params }: { params: Promise<{ file: string }> }): Promise<Response> {
  const name = NAME.exec((await params).file)?.[1]
  const entries = name ? (await sitemapGroups()).get(name) : undefined
  if (!entries) return new Response('Not found', { status: 404 })
  return new Response(urlsetXml(entries), { headers: { 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': 'public, max-age=300' } })
}
