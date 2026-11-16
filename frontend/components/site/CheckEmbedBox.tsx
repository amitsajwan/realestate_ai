'use client'

import React, { useState } from 'react'
import { checkEmbed } from '@/lib/site/checkEmbed'

/** On /check: the check for other websites, shown as it will look, with its code and a copy button. */
export default function CheckEmbedBox({ siteUrl }: { siteUrl: string }) {
  const code = checkEmbed(siteUrl)
  const [done, setDone] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setDone(true)
      setTimeout(() => setDone(false), 2500)
    } catch {
      window.prompt?.('Copy this code', code)
    }
  }
  return (
    <section aria-labelledby="embed-title" className="mt-10 rounded-xl border border-slate-200 p-4" data-testid="check-embed">
      <h2 id="embed-title" className="text-lg font-semibold text-slate-900">Put this check on your website</h2>
      <p className="mt-1 text-sm text-slate-600">
        Free for housing societies, blogs and agents. Paste the code into any page: it works without scripts and opens the results here.
      </p>
      {/* the same HTML the visitor copies, drawn as it will look on their page */}
      <div className="mt-4" dangerouslySetInnerHTML={{ __html: code }} />
      <label htmlFor="embed-code" className="mt-4 block text-sm font-medium text-slate-900">Code to paste</label>
      <textarea id="embed-code" readOnly value={code} rows={5} className="mt-1 w-full rounded-lg border border-slate-300 p-2 font-mono text-xs text-slate-700"
        onFocus={(e) => e.currentTarget.select()} />
      <button type="button" onClick={copy} className="mt-2 inline-flex min-h-[44px] items-center rounded-lg bg-[#0f2340] px-4 font-semibold text-white">
        {done ? '✓ Code copied' : 'Copy the code'}
      </button>
    </section>
  )
}
