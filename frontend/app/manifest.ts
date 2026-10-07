import type { MetadataRoute } from 'next'
import { BRAND_NAME, DEFAULT_DESCRIPTION, LOGO, NAVY } from '@/lib/brand'

/** Web app manifest (served at /manifest.webmanifest and linked from every page by Next). */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: BRAND_NAME,
    short_name: BRAND_NAME,
    description: DEFAULT_DESCRIPTION,
    start_url: '/',
    display: 'browser',
    background_color: NAVY,
    theme_color: NAVY,
    icons: [
      { src: LOGO.icon192, sizes: '192x192', type: 'image/png' },
      { src: LOGO.icon512, sizes: '512x512', type: 'image/png' },
    ],
  }
}
