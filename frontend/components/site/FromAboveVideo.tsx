'use client'

import React, { useEffect, useRef, useState } from 'react'

/** The month-by-month loop of a site from above. It loads only once it is near the screen (most visitors never scroll this
 *  far, and the file is about a megabyte), plays muted and loops, and stops when scrolled away. Until then the poster, the
 *  latest month, stands in. */
export default function FromAboveVideo({ src, poster, width, height, label }: {
  src: string; poster: string; width: number; height: number; label: string
}) {
  const ref = useRef<HTMLVideoElement>(null)
  const [near, setNear] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el || typeof IntersectionObserver === 'undefined') return
    const seen = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          setNear(true)
          el.play?.()?.catch(() => {})
        } else {
          el.pause?.()
        }
      }
    }, { rootMargin: '200px 0px' })
    seen.observe(el)
    return () => seen.disconnect()
  }, [])

  return (
    <video ref={ref} poster={poster} width={width} height={height} muted loop playsInline autoPlay={near}
      preload="none" aria-label={label} className="h-auto w-full rounded-lg border border-slate-200 bg-slate-900"
      src={near ? src : undefined} data-testid="from-above-video" />
  )
}
