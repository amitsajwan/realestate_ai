import React from 'react'
import type { BuilderLogo } from '@/lib/site/register'

// The builder's own logo in a fixed box (backend areastats/logos.py): on white, or on navy when the logo is drawn for a dark
// header. The builders list and builder pages use it so a list of names is not only text (owner 2026-10-31).
export default function BuilderLogoMark({ logo, name, size = 'md' }: { logo: BuilderLogo; name: string; size?: 'sm' | 'md' | 'lg' }) {
  const box = size === 'sm' ? 'h-8 w-20 p-1' : size === 'lg' ? 'h-20 w-48 p-3' : 'h-12 w-28 p-1.5'
  return (
    <span className={`inline-flex shrink-0 items-center justify-center rounded-lg border border-slate-200 ${box} ${logo.tone === 'light' ? 'bg-[#16305a]' : 'bg-white'}`}
      data-testid="builder-logo">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={logo.url} alt={`${name} logo`} width={logo.width ?? undefined} height={logo.height ?? undefined}
        loading="lazy" decoding="async" className="max-h-full max-w-full object-contain" />
    </span>
  )
}
