'use client'

import React, { useState } from 'react'
import type { Lang } from '@/lib/site/types'

const LABELS: Record<Lang, string> = { en: 'English', hi: 'हिन्दी', mr: 'मराठी' }
const ORDER: Lang[] = ['en', 'hi', 'mr']

export function availableLangs(d: { en?: string; hi?: string; mr?: string }): Lang[] {
  return ORDER.filter((l) => !!(d[l] && String(d[l]).trim()))
}

export default function DescriptionSwitch({ description }: { description: { en?: string; hi?: string; mr?: string } }) {
  const langs = availableLangs(description)
  const [lang, setLang] = useState<Lang>(langs[0] || 'en')
  if (langs.length === 0) return null
  return (
    <section aria-labelledby="desc-title">
      <div className="flex items-center justify-between gap-2">
        <h2 id="desc-title" className="text-lg font-bold">About this property</h2>
        {langs.length > 1 && (
          <div role="group" aria-label="Description language" className="flex gap-1">
            {langs.map((l) => (
              <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)}
                className={'min-h-[44px] min-w-[44px] rounded-full border px-3 text-sm font-semibold ' +
                  (lang === l ? 'border-[var(--site-primary)] bg-[var(--site-primary)] text-[var(--site-on-primary)]' : 'border-slate-300 bg-white text-slate-700')}>
                {LABELS[l]}
              </button>
            ))}
          </div>
        )}
      </div>
      <p lang={lang} className="mt-2 whitespace-pre-line leading-relaxed text-slate-800">{description[lang]}</p>
    </section>
  )
}
