import React from 'react'
import Link from 'next/link'
import { TEAM, teamAddress } from '@/lib/site/team'

/**
 * Who answers for Avasetu, in the main site's footer: House Deal's office, phone, email and MahaRERA number (lib/site/team).
 * Not on an agent's own site (components/site/SiteShell), whose footer is that agent's.
 */
export default function TeamBlock() {
  const a = 'font-semibold text-[#0f2340] underline underline-offset-4'
  return (
    <div data-testid="team-block" className="mt-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-600">The team</h2>
      <address className="mt-2 max-w-md not-italic text-slate-800">
        <a href={TEAM.page} className={a}>{TEAM.name}</a>, MahaRERA agent {TEAM.rera}<br />
        {teamAddress()}<br />
        <a href={`tel:${TEAM.tel}`} className={a}>{TEAM.phone}</a> · <a href={`mailto:${TEAM.email}`} className={a}>{TEAM.email}</a>
      </address>
      <p className="mt-2"><Link href="/contact" className={a}>Contact us</Link></p>
    </div>
  )
}
