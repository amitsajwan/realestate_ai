'use client'

import React, { useEffect, useState } from 'react'
import { COMPARE_MAX, PICKS_EVENT, readPicks, togglePick } from '@/lib/site/picks'
import type { PickList } from '@/lib/site/picks'

/** The browser's list, redrawn when any button or the bar changes it. Empty until mounted, so the server's HTML and the first
 *  client render agree. */
export function usePicks(list: PickList): string[] {
  const [slugs, setSlugs] = useState<string[]>([])
  useEffect(() => {
    const read = () => setSlugs(readPicks(list))
    read()
    window.addEventListener(PICKS_EVENT, read)
    window.addEventListener('storage', read)
    return () => {
      window.removeEventListener(PICKS_EVENT, read)
      window.removeEventListener('storage', read)
    }
  }, [list])
  return slugs
}

const BASE = 'inline-flex min-h-[44px] items-center gap-1.5 rounded-xl border px-3 text-sm font-semibold'

/** "+ Compare" and "Save" for one project, on its page and on its cards. `dark` for the project page's dark hero. */
export default function PickButtons({ slug, name, dark = false }: { slug: string; name: string; dark?: boolean }) {
  const compare = usePicks('compare')
  const saved = usePicks('saved')
  const inCompare = compare.includes(slug)
  const isSaved = saved.includes(slug)
  const tone = (on: boolean) => on
    ? (dark ? 'border-amber-300 bg-amber-300 text-slate-900' : 'border-[#0f2340] bg-[#0f2340] text-white')
    : (dark ? 'border-white/40 bg-transparent text-white' : 'border-slate-300 bg-white text-[#0f2340]')
  return (
    <div className="flex flex-wrap gap-2" data-testid="pick-buttons">
      <button type="button" aria-pressed={inCompare} onClick={() => togglePick('compare', slug)} className={`${BASE} ${tone(inCompare)}`}
        title={inCompare ? `Take ${name} out of the comparison` : `Compare ${name} with up to ${COMPARE_MAX - 1} others`} data-testid="pick-compare">
        <span aria-hidden>{inCompare ? '✓' : '+'}</span> {inCompare ? 'Comparing' : 'Compare'}
      </button>
      <button type="button" aria-pressed={isSaved} onClick={() => togglePick('saved', slug)} className={`${BASE} ${tone(isSaved)}`}
        title={isSaved ? `Take ${name} off your shortlist` : `Save ${name} to your shortlist`} data-testid="pick-save">
        <span aria-hidden>{isSaved ? '♥' : '♡'}</span> {isSaved ? 'Saved' : 'Save'}
      </button>
    </div>
  )
}
