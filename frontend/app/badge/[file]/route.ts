import { badgeSvg } from '@/lib/site/badge'
import { displayName, getRegisterProjectByRegno } from '@/lib/site/register'

// Drawn when asked (the register is not there at build time); the picture is kept a day by browsers and the CDN in front of sites
export const dynamic = 'force-dynamic'

type Props = { params: Promise<{ file: string }> }

/** /badge/<MahaRERA number>.svg: the "Checked on MahaRERA" badge for a project in our register (lib/site/badge.ts). A number we do
 *  not hold is a 404, never a badge that vouches for a project we have not read. */
export async function GET(_req: Request, { params }: Props): Promise<Response> {
  const { file } = await params
  const m = /^(P[A-Z0-9]{6,20})\.svg$/i.exec(file || '')
  const p = m ? await getRegisterProjectByRegno(m[1].toUpperCase()).catch(() => null) : null
  if (!p) return new Response('Not found', { status: 404, headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'public, max-age=300' } })
  const svg = badgeSvg({ name: displayName(p), regno: p.regno, checked: p.details_read_at ?? p.page_updated ?? null })
  return new Response(svg, { headers: { 'Content-Type': 'image/svg+xml; charset=utf-8', 'Cache-Control': 'public, max-age=86400',
    'X-Robots-Tag': 'noindex' } })
}
