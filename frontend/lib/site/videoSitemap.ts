import type { FromSpaceItem } from '@/lib/site/register'

/** Google's video sitemap for the "from space" timelapses (backend areastats.fromabove): one <url> per project page with its
 *  <video:video>, so the video can show in Google's video results and on the page's own result. Only what the page shows. */
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

export function videoSitemapXml(base: string, items: FromSpaceItem[]): string {
  const rows = items.filter((x) => x.video).map((x) => {
    const v = x.video!
    const title = `${x.name} from space, ${x.years[0]} to ${x.years[1]}`
    return `<url><loc>${esc(`${base}/projects/${x.slug}`)}</loc><video:video>` +
      `<video:thumbnail_loc>${esc(base + v.poster)}</video:thumbnail_loc><video:title>${esc(title)}</video:title>` +
      `<video:description>${esc(x.story.slice(0, 2000))}</video:description><video:content_loc>${esc(base + v.src)}</video:content_loc>` +
      (x.updated ? `<video:publication_date>${x.updated}</video:publication_date>` : '') +
      `<video:family_friendly>yes</video:family_friendly></video:video></url>`
  })
  return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" ' +
    `xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n${rows.join('\n')}\n</urlset>\n`
}
