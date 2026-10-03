import React from 'react'

/**
 * Carousel slides in a swipeable row, the way they read on Instagram: 4:5 frames, scroll-snap, the next slide peeking in.
 * No script: native horizontal scroll works with touch, trackpad and keyboard (the row is focusable).
 */
export default function SlideStrip({ slides, label, size = 'md', className = '' }: {
  slides: { url: string; alt: string }[]; label: string; size?: 'sm' | 'md'; className?: string
}) {
  if (!slides.length) return null
  const w = size === 'sm' ? 'w-[86%]' : 'w-[78%] sm:w-[46%] lg:w-[31%]'
  return (
    <div className={className}>
      <ul tabIndex={0} aria-label={label} data-testid="slide-strip"
        className="flex snap-x snap-mandatory gap-3 overflow-x-auto pb-2 [scrollbar-width:thin] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--site-primary,#0f2340)]">
        {slides.map((s, i) => (
          <li key={s.url} className={'flex-none snap-start list-none ' + w}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={s.url} alt={s.alt} width={1080} height={1350} loading={i === 0 ? 'eager' : 'lazy'} decoding="async"
              className="aspect-[4/5] h-auto w-full rounded-xl border border-slate-200 bg-slate-100 object-cover" />
          </li>
        ))}
      </ul>
      {slides.length > 1 && <p className="mt-1 text-xs text-slate-500">{slides.length} slides · swipe</p>}
    </div>
  )
}
