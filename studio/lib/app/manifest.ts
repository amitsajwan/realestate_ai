/** Studio's web app manifest (served at /studio/manifest.webmanifest by app/studio/manifest.webmanifest/route.ts): what the phone
 *  installs. Its own id and scope (/studio), apart from the site's manifest, which installs the project check (/check). */
import type { MetadataRoute } from 'next'
import { BRAND_NAME, LOGO, NAVY } from '@shared/brand'

export const MANIFEST_PATH = '/studio/manifest.webmanifest'

export function studioManifest(): MetadataRoute.Manifest {
  return {
    id: '/studio',
    name: `${BRAND_NAME} Studio`,
    short_name: 'Studio',
    description: 'Your leads, listings and posts. Rings when a buyer is waiting.',
    start_url: '/studio?src=app',
    scope: '/studio',
    display: 'standalone',
    orientation: 'portrait',
    background_color: '#ffffff',
    theme_color: NAVY,
    icons: [
      { src: LOGO.icon192, sizes: '192x192', type: 'image/png' },
      { src: LOGO.icon512, sizes: '512x512', type: 'image/png' },
    ],
    // a long press on the home-screen icon (Android)
    shortcuts: [
      { name: 'Add listing', url: '/studio/listings/new', icons: [{ src: LOGO.icon192, sizes: '192x192' }] },
      { name: 'Leads', url: '/studio/leads', icons: [{ src: LOGO.icon192, sizes: '192x192' }] },
    ],
  }
}
