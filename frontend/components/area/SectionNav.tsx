'use client'
import React, { useEffect, useRef, useState } from 'react'

export type SectionLink = { id: string; label: string }

/** "On this page": the area page's sections as tabs that jump, not tabs that hide. Every section stays on the page, rendered on the
 *  server, so Google reads one whole page and a reader can scroll it end to end; the bar only takes them there. Plain anchors, so it
 *  works before JavaScript loads and each section has an address to share (`#map`). Sticky under the site header on a phone (a row
 *  that scrolls sideways), a column beside the page on a laptop. The section being read is marked (`aria-current`). */
export default function SectionNav({ items, className = '' }: { items: SectionLink[]; className?: string }) {
  const [active, setActive] = useState<string | undefined>(items[0]?.id)
  const bar = useRef<HTMLUListElement>(null)
  const ids = items.map((i) => i.id).join(' ')

  useEffect(() => {
    // the section being read is the last one whose top has passed under the bars (the site header and this one, or 120 px);
    // at the very bottom of the page, the last section, which may be too short to reach the top
    let frame = 0
    const mark = () => {
      frame = 0
      const tops = ids.split(' ').map((id) => [id, document.getElementById(id)?.getBoundingClientRect().top] as const)
      const passed = tops.filter(([, top]) => top != null && top <= 130)
      const atEnd = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4
      const id = atEnd && window.scrollY > 0 ? tops[tops.length - 1][0] : passed.length ? passed[passed.length - 1][0] : tops[0]?.[0]
      if (id) setActive(id)
    }
    const onScroll = () => { if (!frame) frame = window.requestAnimationFrame(mark) }
    mark()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      if (frame) window.cancelAnimationFrame(frame)
    }
  }, [ids])

  useEffect(() => {
    // keep the marked tab in sight on a phone's sideways row, without moving the page
    const ul = bar.current
    const tab = ul?.querySelector<HTMLElement>(`[data-section="${active}"]`)
    if (ul && tab && ul.scrollWidth > ul.clientWidth && typeof ul.scrollTo === 'function') ul.scrollTo({ left: tab.offsetLeft - 16, behavior: 'smooth' })
  }, [active])

  if (items.length < 2) return null
  return (
    <nav aria-label="On this page" data-testid="section-nav" data-print="hide"
      className={`${className} sticky top-[57px] z-20 -mx-4 border-b border-slate-200 bg-white/95 px-4 backdrop-blur lg:top-24 lg:mx-0 lg:self-start lg:border-0 lg:bg-transparent lg:px-0 lg:backdrop-blur-none`}>
      <p className="hidden text-xs font-bold uppercase tracking-wider text-slate-500 lg:block">On this page</p>
      <ul ref={bar} className="flex list-none gap-1 overflow-x-auto p-0 py-2 [scrollbar-width:none] lg:mt-2 lg:flex-col lg:gap-0.5 lg:overflow-visible lg:py-0 [&::-webkit-scrollbar]:hidden">
        {items.map((i) => (
          <li key={i.id} className="shrink-0">
            <a href={`#${i.id}`} data-section={i.id} aria-current={active === i.id ? 'location' : undefined}
              onClick={() => setActive(i.id)}
              className={'flex min-h-[40px] items-center whitespace-nowrap rounded-full px-3.5 text-sm font-semibold no-underline lg:rounded-lg lg:px-3 ' +
                (active === i.id ? 'bg-[#0f2340] text-white' : 'text-[#0f2340] hover:bg-slate-100')}>
              {i.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
