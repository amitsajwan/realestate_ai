'use client'

import { useEffect, useState } from 'react'
import { getToken } from '@shared/session'

/** For a signed-in agent reading a project's page: start a listing from it. Buyers never see it. A plain link: Studio is the other app. */
export default function ListThisProject({ regno }: { regno: string }) {
  const [agent, setAgent] = useState(false)
  useEffect(() => {
    try { setAgent(!!getToken()) } catch { /* a browser with no storage is a buyer */ }
  }, [])
  if (!agent) return null
  return (
    <a href={`/studio/listings/new?project=${encodeURIComponent(regno)}`} data-testid="list-this-project"
      className="mt-3 inline-flex min-h-[44px] items-center rounded-full border-2 border-[#0f2340] px-4 font-bold text-[#0f2340] no-underline">
      List this project
    </a>
  )
}
