/** A post's text for its page: paragraphs of lines, where only links to our own site become links (as site paths). */

export type Piece = { text: string } | { text: string; href: string }

/** The path of a URL on our own site ('https://avasetu.in/localities/wagholi' -> '/localities/wagholi'), else null. */
export function ownPath(url: string | null | undefined, siteUrl: string): string | null {
  if (!url) return null
  const site = siteUrl.replace(/\/+$/, '')
  if (!url.startsWith(site + '/')) return null
  const path = url.slice(site.length)
  return /^\/[^\s"'<>\\]*$/.test(path) && !path.startsWith('//') ? path : null
}

/** The project page a post points to, when its site link is one. */
export function projectPath(siteUrlOfPost: string | null | undefined, siteUrl: string): string | null {
  const path = ownPath(siteUrlOfPost, siteUrl)
  return path && /^\/(?:agent\/[^/]+\/)?projects\/[^/?#]+\/?$/.test(path) ? path : null
}

const URL_RE = /https?:\/\/[^\s]+/g

function line(text: string, siteUrl: string): Piece[] {
  const out: Piece[] = []
  let at = 0
  for (const m of text.matchAll(URL_RE)) {
    const raw = m[0].replace(/[.,;:)]+$/, '')
    const start = m.index ?? 0
    const href = ownPath(raw, siteUrl)
    if (!href) continue // not ours: left as plain text
    if (start > at) out.push({ text: text.slice(at, start) })
    out.push({ text: raw.replace(/^https?:\/\//, ''), href })
    at = start + raw.length
  }
  if (at < text.length) out.push({ text: text.slice(at) })
  return out
}

/** Paragraphs (split at blank lines), each a list of lines, each a list of pieces. */
export function postParagraphs(text: string, siteUrl: string): Piece[][][] {
  return (text || '').split(/\n\s*\n/).map((p) => p.split('\n').map((l) => l.trim()).filter(Boolean))
    .filter((p) => p.length).map((p) => p.map((l) => line(l, siteUrl)))
}

const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()

/** The text without its first line when that line is the title (the page shows the title as its heading). */
export function withoutTitle(text: string, title: string): string {
  const lines = (text || '').split('\n')
  const i = lines.findIndex((l) => l.trim())
  const t = norm(title.replace(/…$/, ''))
  return i >= 0 && t && norm(lines[i]).startsWith(t) ? lines.slice(i + 1).join('\n').trim() : (text || '').trim()
}
