import type { FromSpaceItem } from '@/lib/site/register'
import { areaFromSpacePath, type AreaFromSpaceItem } from '@/lib/site/areaFromSpace'

/** Google's video sitemap for the "from space" timelapses (backend areastats.fromabove and areaspace): one <url> per
 *  project's watch page (/projects/<slug>/from-space, where the video is the main thing, as Google asks before it shows a
 *  video result) and per area's (/localities/<slug>/from-space), each with its <video:video>. Only what the page shows. */
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

type Row = { path: string; title: string; story: string; video: NonNullable<FromSpaceItem['video']>; updated: string | null }

export function videoSitemapXml(base: string, items: FromSpaceItem[], areas: AreaFromSpaceItem[] = []): string {
  const all: Row[] = [
    ...areas.filter((x) => x.video).map((x) => ({ path: areaFromSpacePath(x.slug), title: `${x.name}, Pune from space, ${x.years[0]} to ${x.years[1]}`,
      story: x.story, video: x.video!, updated: x.updated })),
    ...items.filter((x) => x.video).map((x) => ({ path: `/projects/${x.slug}/from-space`, title: `${x.name} from space, ${x.years[0]} to ${x.years[1]}`,
      story: x.story, video: x.video!, updated: x.updated })),
  ]
  const rows = all.map((x) => {
    const v = x.video
    return `<url><loc>${esc(base + x.path)}</loc><video:video>` +
      `<video:thumbnail_loc>${esc(base + v.poster)}</video:thumbnail_loc><video:title>${esc(x.title)}</video:title>` +
      `<video:description>${esc(x.story.slice(0, 2000))}</video:description><video:content_loc>${esc(base + v.src)}</video:content_loc>` +
      (x.updated ? `<video:publication_date>${x.updated}</video:publication_date>` : '') +
      `<video:family_friendly>yes</video:family_friendly></video:video></url>`
  })
  return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" ' +
    `xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n${rows.join('\n')}\n</urlset>\n`
}
