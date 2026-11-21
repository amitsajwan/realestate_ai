import QRCode from 'qrcode'
import { badgeName } from './badge'

/**
 * The printable QR card for a project page (docs/plan/visibility-base.md step 4, "QR codes"): House Deal prints it for the office
 * and site-visit sheets, a buyer standing at the site scans it and lands on the project's checked page. The link carries src=qr,
 * so those visits and enquiries are counted as "QR code" (Studio's lead sources). Black on white with a quiet zone and error
 * correction M, so it scans from paper and from a photo of the paper.
 */

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const QUIET = 4
const CELL = 8

/** The address the code opens: the project's page, tagged as a scan. */
export function qrTarget(siteUrl: string, slug: string): string {
  return `${siteUrl.replace(/\/$/, '')}/projects/${slug}?src=qr`
}

/** The card: the code, then the project's name, its MahaRERA number and what the page holds. */
export function qrSvg({ url, name, regno }: { url: string; name: string; regno: string }): string {
  const { modules } = QRCode.create(url, { errorCorrectionLevel: 'M' })
  const n = modules.size
  const side = (n + 2 * QUIET) * CELL
  let path = ''
  for (let y = 0; y < n; y++) {
    for (let x = 0; x < n; x++) {
      if (modules.get(y, x)) path += `M${(x + QUIET) * CELL} ${(y + QUIET) * CELL}h${CELL}v${CELL}h-${CELL}z`
    }
  }
  const h = side + 96
  const title = `${name}: scan for the price, possession date and homes booked (MahaRERA ${regno})`
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${side}" height="${h}" viewBox="0 0 ${side} ${h}" role="img" aria-label="${esc(title)}">` +
    `<title>${esc(title)}</title>` +
    `<rect width="${side}" height="${h}" fill="#ffffff"/>` +
    `<path d="${path}" fill="#000000" shape-rendering="crispEdges"/>` +
    '<g font-family="Segoe UI,Roboto,Helvetica,Arial,sans-serif" text-anchor="middle">' +
    `<text x="${side / 2}" y="${side + 22}" font-size="20" font-weight="700" fill="#0f2340">${esc(badgeName(name, 32))}</text>` +
    `<text x="${side / 2}" y="${side + 48}" font-size="15" fill="#334155">Price, possession date and homes booked</text>` +
    `<text x="${side / 2}" y="${side + 72}" font-size="13" fill="#64748b">MahaRERA ${esc(regno)} · avasetu.in</text>` +
    '</g></svg>'
}
