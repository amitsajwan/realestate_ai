import { serverApiBase } from './api'
import type { AgentVideo, MainVideo } from './register'

/** A project page with videos we keep (backend propertyfacts, `GET /public/project-videos`): the listing's campaign video
 *  (mainvideo.py) and the agent's own videos copied to our server (agentvideos.py). */
export interface ProjectVideoItem {
  slug: string
  name: string
  video?: MainVideo | null
  agent_videos?: AgentVideo[] | null
}

/** One video on its own watch page: the page's address, its words for search, and the video as the player takes it. */
export interface WatchVideo {
  key: string | null
  path: string
  title: string
  description: string
  video: MainVideo
  portrait: boolean
}

/** The watch page of a project's video: the video is its main content, which is what Google shows in video results. The
 *  first video of a project is at /video, each further one at /video/<key>. */
export const videoPagePath = (slug: string, key?: string | null): string =>
  key ? `/projects/${slug}/video/${key}` : `/projects/${slug}/video`

const agentTitle = (name: string, label: string): string => {
  const what = (label || 'Video').trim()
  return `${name}: ${/video/i.test(what) ? what : `${what} video`}`
}

/** A project's videos in watch-page order: the campaign video first, then the agent's in the listing's order. The first one
 *  has the project's /video page; each later agent video its own /video/<key>. */
export function watchVideos(slug: string, name: string, main?: MainVideo | null, agent?: AgentVideo[] | null): WatchVideo[] {
  const out: Omit<WatchVideo, 'path'>[] = []
  if (main?.url) {
    out.push({
      key: null, title: `${name}: homes, prices and MahaRERA details`, portrait: true, video: main,
      description: main.headline || `A short video of ${name}, Pune: the homes, the prices and the MahaRERA registration.`,
    })
  }
  for (const a of agent ?? []) {
    if (!a?.url || !a.key) continue
    const label = (a.label || '').trim()
    out.push({
      key: a.key, title: agentTitle(name, label),
      description: `${label ? `${label} of ${name}` : `A video of ${name}`}, Pune, filmed by the agent who lists it.`,
      portrait: !(a.width && a.height && a.width > a.height),
      video: { url: a.url, poster: a.poster ?? null, seconds: a.seconds ?? null, headline: label, uploaded_at: a.uploaded_at ?? null },
    })
  }
  return out.map((w, i) => ({ ...w, key: i === 0 ? null : w.key, path: videoPagePath(slug, i === 0 ? null : w.key) }))
}

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
    return (data.items ?? []).filter((x) => x?.slug && (x.video?.url || x.agent_videos?.length))
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
  const rows = items.flatMap((x) => watchVideos(x.slug, x.name || x.slug, x.video, x.agent_videos)).filter((w) => w.video.poster).map((w) => {
    const v = w.video
    const tags = [
      `<video:thumbnail_loc>${esc(site + v.poster)}</video:thumbnail_loc>`,
      `<video:title>${esc(w.title.slice(0, 100))}</video:title>`,
      `<video:description>${esc(w.description.slice(0, 2048))}</video:description>`,
      `<video:content_loc>${esc(site + v.url)}</video:content_loc>`,
      v.seconds ? `<video:duration>${Math.round(v.seconds)}</video:duration>` : '',
      v.uploaded_at ? `<video:publication_date>${esc(v.uploaded_at)}</video:publication_date>` : '',
      '<video:family_friendly>yes</video:family_friendly>',
    ].filter(Boolean).join('')
    return `<url><loc>${esc(site + w.path)}</loc><video:video>${tags}</video:video></url>`
  })
  return '<?xml version="1.0" encoding="UTF-8"?>\n'
    + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n'
    + rows.join('\n') + '\n</urlset>\n'
}
