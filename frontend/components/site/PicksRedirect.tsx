'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { comparePath, readPicks, shortlistPath } from '@/lib/site/picks'
import type { PickList } from '@/lib/site/picks'

/** /compare or /shortlist opened with nothing in the link (the menu, a bookmark): this browser's picks fill it, so the page and
 *  the link it shares show the list the buyer made. Renders nothing. */
export default function PicksRedirect({ list }: { list: PickList }) {
  const router = useRouter()
  useEffect(() => {
    const picks = readPicks(list)
    if (list === 'compare' ? picks.length >= 1 : picks.length) router.replace(list === 'compare' ? comparePath(picks) : shortlistPath(picks))
  }, [list, router])
  return null
}
