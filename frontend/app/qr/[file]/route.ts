import { getMarketingConfig } from '@/lib/marketing/config'
import { qrSvg, qrTarget } from '@/lib/site/qr'
import { displayName, getRegisterProject } from '@/lib/site/register'

// Drawn when asked (the register is not there at build time)
export const dynamic = 'force-dynamic'

type Props = { params: Promise<{ file: string }> }

/** /qr/<project slug>.svg: the printable QR card for a project page (lib/site/qr.ts). An unknown project is a 404, never a code
 *  that leads nowhere. Out of search: it is a picture to print, not a page. */
export async function GET(_req: Request, { params }: Props): Promise<Response> {
  const { file } = await params
  const m = /^([a-z0-9]+(?:-[a-z0-9]+){0,15})\.svg$/.exec(file || '')
  const p = m ? await getRegisterProject(m[1]).catch(() => null) : null
  if (!p) return new Response('Not found', { status: 404, headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'public, max-age=300' } })
  const svg = qrSvg({ url: qrTarget(getMarketingConfig().siteUrl, p.slug), name: displayName(p), regno: p.regno })
  return new Response(svg, { headers: { 'Content-Type': 'image/svg+xml; charset=utf-8', 'Cache-Control': 'public, max-age=86400',
    'Content-Disposition': `inline; filename="${p.slug}-qr.svg"`, 'X-Robots-Tag': 'noindex' } })
}
