'use client'

import { useEffect, useRef } from 'react'

const PHONE = '(max-width: 767px)'   // below md: the strip shows one project at a time (app/globals.css)
const HOLD_MS = 5000                 // time to read one project before the next slides in

/** Phones only: moves the hot strip to its next project every few seconds. The strip is a scroll-snap row there, so a swipe
 *  works too; a finger on it pauses the stepping and a swipe by hand stops it for good. Renders nothing; does nothing on a
 *  laptop (the CSS loop rolls there) or with reduced motion. */
export default function HotStripStepper() {
  const mark = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const strip = mark.current?.closest('.hot-strip')
    const viewport = strip?.querySelector<HTMLElement>('.hot-strip-viewport')
    if (!viewport || typeof window.matchMedia !== 'function') return
    if (!window.matchMedia(PHONE).matches || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const entries = Array.from(viewport.querySelectorAll<HTMLElement>('.hot-strip-row:first-child > li'))
    if (entries.length < 2) return
    let touching = false
    let stopped = false
    const down = () => { touching = true }
    const up = () => { touching = false }
    const swiped = () => { if (touching) stopped = true }
    viewport.addEventListener('touchstart', down, { passive: true })
    viewport.addEventListener('touchend', up, { passive: true })
    viewport.addEventListener('scroll', swiped, { passive: true })
    const timer = window.setInterval(() => {
      if (stopped || touching || document.hidden) return
      const at = Math.round(viewport.scrollLeft / viewport.clientWidth)
      const next = (at + 1) % entries.length
      viewport.scrollTo({ left: entries[next].offsetLeft - entries[0].offsetLeft, behavior: next ? 'smooth' : 'auto' })
    }, HOLD_MS)
    return () => {
      window.clearInterval(timer)
      viewport.removeEventListener('touchstart', down)
      viewport.removeEventListener('touchend', up)
      viewport.removeEventListener('scroll', swiped)
    }
  }, [])

  return <span ref={mark} hidden />
}
