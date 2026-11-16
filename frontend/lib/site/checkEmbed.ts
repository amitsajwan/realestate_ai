/**
 * "Check a Pune project on MahaRERA" for other people's websites (docs/plan/visibility-base.md step 3: a free tool earns links by
 * itself). Plain HTML with inline styles: a search form that opens our /check results and a plain, followed link to /check. No
 * script and no iframe, so blogs, WordPress posts and housing-society sites that strip both still show it.
 */

/** The HTML a site owner pastes. `siteUrl` is the public site's address. */
export function checkEmbed(siteUrl: string): string {
  const base = siteUrl.replace(/\/$/, '')
  return [
    `<form action="${base}/check" method="get" target="_blank" rel="noopener" style="max-width:420px;padding:14px;border:1px solid #d6dbe4;border-radius:12px;font-family:system-ui,sans-serif;background:#fff">`,
    `<label for="avasetu-check-q" style="display:block;font-weight:600;color:#0f2340;margin-bottom:8px">Check a Pune project on MahaRERA</label>`,
    `<div style="display:flex;gap:8px">`,
    `<input id="avasetu-check-q" name="q" type="search" required minlength="2" placeholder="Project name or MahaRERA number" style="flex:1;min-width:0;padding:9px 10px;border:1px solid #c3cad6;border-radius:8px;font-size:15px" />`,
    `<button type="submit" style="padding:9px 14px;border:0;border-radius:8px;background:#0f2340;color:#fff;font-weight:600;font-size:15px;cursor:pointer">Check</button>`,
    `</div>`,
    `<p style="margin:8px 0 0;font-size:13px;color:#5b6576">Possession date, delays and homes booked, from MahaRERA. <a href="${base}/check" style="color:#0f2340">MahaRERA project check by Avasetu</a></p>`,
    `</form>`,
  ].join('\n')
}
