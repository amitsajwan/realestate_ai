import React from 'react'
import type { Shot } from '@/lib/marketing/strings'

/** A real product screenshot in a simple phone outline. Lazy-loaded unless it is above the fold. */
export default function PhoneFrame({ shot, eager = false, className = '' }: { shot: Shot; eager?: boolean; className?: string }) {
  return (
    <figure className={'mx-auto w-full max-w-[15rem] ' + className}>
      <div className="rounded-[2rem] border-[6px] border-slate-900 bg-slate-900 shadow-xl">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={shot.src}
          alt={shot.alt}
          width={shot.width}
          height={shot.height}
          loading={eager ? 'eager' : 'lazy'}
          decoding="async"
          className="block h-auto w-full rounded-[1.5rem] bg-slate-100"
        />
      </div>
      <figcaption className="mt-3 text-center text-sm text-slate-600">{shot.caption}</figcaption>
    </figure>
  )
}
