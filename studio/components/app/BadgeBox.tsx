'use client'
import React, { useEffect, useState } from 'react'
import { badgeEmbed, badgeUrl } from '@shared/site/badge'

/**
 * "Badge for your website" on a listing with a MahaRERA number (docs/plan/visibility-base.md step 3): the agent pastes it on their
 * own site or blog, and buyers who click it land on the project's checked page. Shown only when the number is in our register
 * (GET /api/v1/public/register/by-regno/<regno> gives the page); otherwise nothing, never a badge for a project we have not read.
 */
export function BadgeBox({ regno, name }: { regno: string; name: string }) {
  const [slug, setSlug] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const n = regno.trim().toUpperCase()

  useEffect(() => {
    if (!/^P[A-Z0-9]{6,20}$/.test(n)) return
    let live = true
    fetch(`/api/v1/public/register/by-regno/${encodeURIComponent(n)}`, { headers: { Accept: 'application/json' } })
      .then((r) => (r.ok ? r.json() : null))
      .then((d: { slug?: string } | null) => { if (live && d?.slug) setSlug(d.slug) })
      .catch(() => {})
    return () => { live = false }
  }, [n])

  if (!slug) return null
  const site = window.location.origin
  const code = badgeEmbed(site, slug, n, name)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch { /* the code stays selectable in the box */ }
  }
  return (
    <section aria-label="Badge for your website" className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" data-testid="badge-box">
      <h2 className="font-bold text-gray-900">Badge for your website</h2>
      <p className="text-sm text-gray-600">
        Paste this on your website or blog. Buyers see the project is registered with MahaRERA, and a tap opens its checked page with
        the price, possession date and homes booked.
      </p>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={badgeUrl(site, n)} width={300} height={64} alt={`${name}: checked on MahaRERA (${n})`} />
      <textarea readOnly value={code} rows={3} onFocus={(e) => e.currentTarget.select()} aria-label="Badge code"
        className="block w-full rounded-lg border border-gray-300 bg-gray-50 p-2 font-mono text-xs text-gray-800" />
      <button type="button" onClick={copy} className="min-h-[44px] rounded-xl border border-[#0f2340] px-4 text-sm font-semibold text-[#0f2340]">
        {copied ? 'Copied' : 'Copy the code'}
      </button>
    </section>
  )
}
