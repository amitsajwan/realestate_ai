/**
 * The "Checked on MahaRERA" badge (docs/plan/visibility-base.md step 3): agents and builders put it on their own sites, linked to
 * the project's page here, which is how a young site earns its first links from sites that sell the same homes. Drawn from the
 * register only: the project's name, its MahaRERA number and the day we last read its record. Nothing a reader cannot check.
 */

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** "Godrej Ivara" cut at a word to fit the badge's line (28 characters). */
export function badgeName(name: string, max = 28): string {
  const n = name.replace(/\s+/g, ' ').trim()
  if (n.length <= max) return n
  const at = n.lastIndexOf(' ', max - 1)
  return (at > max * 0.5 ? n.slice(0, at) : n.slice(0, max - 1)).replace(/[\s,·-]+$/, '') + '…'
}

/** "Nov 2026" from "2026-11-14"; '' when unreadable. */
export function badgeMonth(day: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})/.exec(day || '')
  return m && +m[2] >= 1 && +m[2] <= 12 ? `${MONTHS[+m[2] - 1]} ${m[1]}` : ''
}

/** The badge, 300×64, in the site's colours: a tick, "Checked on MahaRERA", the project and its number, the month we read it. */
export function badgeSvg({ name, regno, checked }: { name: string; regno: string; checked?: string | null }): string {
  const month = badgeMonth(checked)
  const line2 = `${regno}${month ? ` · read ${month}` : ''}`
  const title = `${name}: MahaRERA ${regno}, checked by Avasetu${month ? ` (${month})` : ''}`
  return `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="64" viewBox="0 0 300 64" role="img" aria-label="${esc(title)}">` +
    `<title>${esc(title)}</title>` +
    '<rect width="300" height="64" rx="10" fill="#0f2340"/>' +
    '<circle cx="32" cy="32" r="18" fill="#f0b440"/>' +
    '<path d="M23.5 32.5l6 6 11-12" fill="none" stroke="#0f2340" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>' +
    '<g font-family="Segoe UI,Roboto,Helvetica,Arial,sans-serif">' +
    '<text x="60" y="22" font-size="13" font-weight="700" fill="#f0b440">Checked on MahaRERA</text>' +
    `<text x="60" y="39" font-size="13" font-weight="600" fill="#ffffff">${esc(badgeName(name))}</text>` +
    `<text x="60" y="54" font-size="10.5" fill="#c9d3e3">${esc(line2)} · Avasetu</text>` +
    '</g></svg>'
}

export { badgeEmbed, badgeUrl } from '@shared/site/badge'
