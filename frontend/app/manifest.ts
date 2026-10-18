import type { MetadataRoute } from 'next'
import { BRAND_NAME, LOGO, NAVY } from '@/lib/brand'

/** Web app manifest (served at /manifest.webmanifest and linked from every page by Next). "Add to Home Screen" installs the
 *  project check (docs/plan/project-check.md): it opens on /check, without the browser bar. */
export default function manifest(): MetadataRoute.Manifest {
  return {
    id: '/check',
    name: `${BRAND_NAME}: check your project on MahaRERA`,
    short_name: BRAND_NAME,
    description: 'Search your Pune project and see its possession date on MahaRERA, whether it moved, and how many homes are booked.',
    start_url: '/check?src=app',
    scope: '/',
    display: 'standalone',
    background_color: NAVY,
    theme_color: NAVY,
    icons: [
      { src: LOGO.icon192, sizes: '192x192', type: 'image/png' },
      { src: LOGO.icon512, sizes: '512x512', type: 'image/png' },
    ],
  }
}
