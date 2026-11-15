/**
 * The "Checked on MahaRERA" badge's embed code (docs/plan/visibility-base.md step 3), shared by the public site (which draws the
 * badge at /badge/<regno>.svg) and Studio (which shows agents the code to paste on their own sites). Plain TypeScript.
 */

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

/** The badge picture's address. */
export function badgeUrl(siteUrl: string, regno: string): string {
  return `${siteUrl.replace(/\/$/, '')}/badge/${regno}.svg`
}

/** The HTML an agent pastes: the badge, linked to the project's page (a plain link: a nofollow would waste the point). */
export function badgeEmbed(siteUrl: string, slug: string, regno: string, name: string): string {
  const base = siteUrl.replace(/\/$/, '')
  return `<a href="${base}/projects/${slug}" title="${esc(name)} on MahaRERA, checked by Avasetu">` +
    `<img src="${badgeUrl(base, regno)}" width="300" height="64" alt="${esc(name)}: checked on MahaRERA (${regno})" /></a>`
}
