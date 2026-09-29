'use client'

import React, { useRef, useState } from 'react'
import type { ListingMedia } from '@/lib/site/types'

/** Swipe-friendly gallery: native horizontal scroll-snap (touch swipe), arrows/dots for desktop. */
export default function Gallery({ media, title }: { media: ListingMedia[]; title: string }) {
  const images = media.filter((m) => m.kind === 'image').sort((a, b) => a.order - b.order)
  const scroller = useRef<HTMLDivElement>(null)
  const [idx, setIdx] = useState(0)
  if (images.length === 0) {
    return <div className="flex aspect-[4/3] items-center justify-center bg-slate-100 text-slate-500">No photos yet</div>
  }
  const go = (i: number) => {
    const el = scroller.current
    if (!el) return
    const n = Math.max(0, Math.min(images.length - 1, i))
    el.scrollTo({ left: n * el.clientWidth, behavior: 'smooth' })
    setIdx(n)
  }
  const onScroll = () => {
    const el = scroller.current
    if (el && el.clientWidth) setIdx(Math.round(el.scrollLeft / el.clientWidth))
  }
  return (
    <section aria-roledescription="carousel" aria-label={'Photos of ' + title} className="relative bg-black">
      <div ref={scroller} onScroll={onScroll} tabIndex={0}
        className="flex snap-x snap-mandatory overflow-x-auto scroll-smooth [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {images.map((m, i) => (
          <div key={m.url + i} className="aspect-[4/3] w-full flex-none snap-center md:aspect-[16/9]" role="group" aria-label={'Photo ' + (i + 1) + ' of ' + images.length}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={m.url} alt={title + ' - photo ' + (i + 1)} width={1200} height={800}
              loading={i === 0 ? 'eager' : 'lazy'} decoding="async" className="h-full w-full object-cover" />
          </div>
        ))}
      </div>
      {images.length > 1 && (
        <>
          <button type="button" aria-label="Previous photo" onClick={() => go(idx - 1)}
            className="absolute left-2 top-1/2 hidden h-11 w-11 -translate-y-1/2 rounded-full bg-white/85 text-xl md:block">‹</button>
          <button type="button" aria-label="Next photo" onClick={() => go(idx + 1)}
            className="absolute right-2 top-1/2 hidden h-11 w-11 -translate-y-1/2 rounded-full bg-white/85 text-xl md:block">›</button>
          <span className="absolute bottom-3 right-3 rounded-full bg-black/60 px-3 py-1 text-xs text-white" aria-live="polite">{idx + 1} / {images.length}</span>
        </>
      )}
    </section>
  )
}
