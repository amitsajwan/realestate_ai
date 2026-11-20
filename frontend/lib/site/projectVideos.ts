import { serverApiBase } from './api'
import type { MainVideo } from './register'

/** A project page with our kept listing video (backend propertyfacts mainvideo.py, `GET /public/project-videos`). */
export interface ProjectVideoItem {
  slug: string
  name: string
  video: MainVideo
}

/** The watch page of a project's video: the video is its main content, which is what Google shows in video results. */
export const videoPagePath = (slug: string): string => `/projects/${slug}/video`

/** Every project page with a video, newest first; [] when the API cannot be reached (a sitemap or page then lists none). */
export async function getProjectVideos(): Promise<ProjectVideoItem[]> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 8000)
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/project-videos', {
      headers: { Accept: 'application/json' }, next: { revalidate: 600 }, signal: ctrl.signal,
    })
    if (!res.ok) return []
    const data = (await res.json()) as { items?: ProjectVideoItem[] }
    return (data.items ?? []).filter((x) => x?.slug && x.video?.url)
  } catch {
    return []
  } finally {
    clearTimeout(timer)
  }
}

const esc = (s: string): string =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;')

/** Google's video sitemap: each watch page with its video's picture, title, description, file, length and date. A video with
 *  no picture is left out (Google requires the thumbnail). */
export function projectVideoSitemapXml(base: string, items: ProjectVideoItem[]): string {
  const site = base.replace(/\/$/, '')
  const rows = items.filter((x) => x.video.poster).map((x) => {
    const v = x.video
    const name = x.name || x.slug
    const tags = [
      `<video:thumbnail_loc>${esc(site + v.poster)}</video:thumbnail_loc>`,
      `<video:title>${esc(`${name}: homes, prices and MahaRERA details`.slice(0, 100))}</video:title>`,
      `<video:description>${esc((v.headline || `A short video of ${name}, Pune: the homes, the prices and the MahaRERA registration.`).slice(0, 2048))}</video:description>`,
      `<video:content_loc>${esc(site + v.url)}</video:content_loc>`,
      v.seconds ? `<video:duration>${Math.round(v.seconds)}</video:duration>` : '',
      v.uploaded_at ? `<video:publication_date>${esc(v.uploaded_at)}</video:publication_date>` : '',
      '<video:family_friendly>yes</video:family_friendly>',
    ].filter(Boolean).join('')
    return `<url><loc>${esc(site + videoPagePath(x.slug))}</loc><video:video>${tags}</video:video></url>`
  })
  return '<?xml version="1.0" encoding="UTF-8"?>\n'
    + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n'
    + rows.join('\n') + '\n</urlset>\n'
}
