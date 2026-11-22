import React from 'react'
import { MORE_PROFILES, socialLinks } from '@/lib/marketing/social'
import { BRAND_NAME } from '@/lib/brand'

const ICON = { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'currentColor', 'aria-hidden': true as const, focusable: false as const }

/** Real links to the Avasetu Facebook Page, Instagram and, once it is live (MORE_PROFILES), the LinkedIn company page: people who
 *  come from LinkedIn see the way back. Opens in a new tab. tone = background it sits on. */
export default function SocialStrip({ tone = 'light', className = '' }: { tone?: 'light' | 'dark'; className?: string }) {
  const { facebook, instagram } = socialLinks()
  const linkedin = MORE_PROFILES.find((u) => /^https:\/\/(www\.)?linkedin\.com\/company\/[^/]+/.test(u))
  const base = 'inline-flex min-h-[44px] items-center gap-2 rounded-full border px-4 text-sm font-semibold no-underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2'
  const look = tone === 'dark'
    ? 'border-white/40 text-white hover:bg-white/10 focus-visible:outline-white'
    : 'border-[#0f2340]/40 text-[#0f2340] hover:bg-[#0f2340]/5 focus-visible:outline-[#0f2340]'
  return (
    <ul aria-label={`${BRAND_NAME} on social media`} className={'flex list-none flex-wrap gap-2 p-0 ' + className}>
      <li>
        <a href={facebook} target="_blank" rel="noopener noreferrer" className={base + ' ' + look}>
          <svg {...ICON}><path d="M13.5 21v-8h2.7l.5-3.2h-3.2V7.8c0-.9.4-1.7 1.8-1.7h1.5V3.3S15.5 3 14.2 3C11.6 3 9.9 4.6 9.9 7.4v2.4H7.2V13h2.7v8h3.6z" /></svg>
          Facebook<span className="sr-only"> (opens in a new tab)</span>
        </a>
      </li>
      <li>
        <a href={instagram} target="_blank" rel="noopener noreferrer" className={base + ' ' + look}>
          <svg {...ICON}><path d="M7.5 3h9A4.5 4.5 0 0 1 21 7.5v9a4.5 4.5 0 0 1-4.5 4.5h-9A4.5 4.5 0 0 1 3 16.5v-9A4.5 4.5 0 0 1 7.5 3zm0 1.8A2.7 2.7 0 0 0 4.8 7.5v9a2.7 2.7 0 0 0 2.7 2.7h9a2.7 2.7 0 0 0 2.7-2.7v-9a2.7 2.7 0 0 0-2.7-2.7h-9zM12 7.5a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9zm0 1.8a2.7 2.7 0 1 0 0 5.4 2.7 2.7 0 0 0 0-5.4zm5-2.6a1.05 1.05 0 1 1 0 2.1 1.05 1.05 0 0 1 0-2.1z" /></svg>
          Instagram<span className="sr-only"> (opens in a new tab)</span>
        </a>
      </li>
      {linkedin && (
        <li>
          <a href={linkedin} target="_blank" rel="noopener noreferrer" className={base + ' ' + look}>
            <svg {...ICON}><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.75h4v11.25H3V9.75zm6.5 0h3.8v1.55h.06c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.77 2.65 4.77 6.1V21h-4v-5.1c0-1.22-.02-2.78-1.7-2.78-1.7 0-1.95 1.32-1.95 2.69V21h-4V9.75z" /></svg>
            LinkedIn<span className="sr-only"> (opens in a new tab)</span>
          </a>
        </li>
      )}
    </ul>
  )
}
