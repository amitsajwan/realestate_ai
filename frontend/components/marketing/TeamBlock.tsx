import React from 'react'
import Link from 'next/link'
import { siteTeam } from '@/lib/site/team'

/**
 * Who answers for Avasetu, in the main site's footer: the Avasetu team and its email (lib/site/team, the one place they are
 * set). Not on an agent's own site (components/site/SiteShell), whose footer is that agent's.
 */
export default function TeamBlock() {
  const t = siteTeam()
  const a = 'font-semibold text-[#0f2340] underline underline-offset-4'
  return (
    <div data-testid="team-block" className="mt-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-600">The team</h2>
      <p className="mt-2 max-w-md text-slate-800">
        {t.name}, Pune
        {/* no WhatsApp link in the footer, as before: enquiries go through the form and chat; the number is on /contact */}
        {t.email && <><br /><a href={`mailto:${t.email}`} className={a}>{t.email}</a></>}
      </p>
      <p className="mt-2"><Link href="/contact" className={a}>Contact us</Link></p>
    </div>
  )
}
