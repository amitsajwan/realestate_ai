'use client'
import React, { useState } from 'react'
import { Btn, ErrorBox, Spinner } from '@/components/app/ui'
import { api, errorMessage } from '@/lib/app/client'
import type { AskAiLine, AskAiPrompt, DraftLanguage, Listing } from '@/lib/app/types'
import { useAsync } from '@/lib/app/useAsync'

const MAX_HIGHLIGHTS = 6 // listings/about.py

const LANGS: Array<[DraftLanguage, string]> = [['en', 'English'], ['mr', 'मराठी'], ['hi', 'हिन्दी']]

/** ChatGPT and Claude take the prompt in the link; Gemini does not, so its button copies the prompt first. */
const AIS: Array<{ name: string; url: (q: string) => string; copy?: boolean }> = [
  { name: 'ChatGPT', url: (q) => `https://chatgpt.com/?q=${encodeURIComponent(q)}` },
  { name: 'Claude', url: (q) => `https://claude.ai/new?q=${encodeURIComponent(q)}` },
  { name: 'Gemini', url: () => 'https://gemini.google.com/app', copy: true },
]

const STATUS: Record<AskAiLine['status'], { label: (l: AskAiLine) => string; cls: string }> = {
  checked: { label: () => 'In our records', cls: 'bg-green-100 text-green-800' },
  builder: { label: () => "Builder's brochure says", cls: 'bg-blue-100 text-blue-800' },
  unchecked: { label: (l) => `Not found: ${l.missing.join(', ')}`, cls: 'bg-red-100 text-red-800' },
  words: { label: () => 'No numbers: check it is true', cls: 'bg-gray-100 text-gray-700' },
}

async function copy(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

/** Ask AI: the agent's own ChatGPT, Claude or Gemini, used by hand. Our prompts go out with the listing's facts; the answer
 *  is pasted back and checked line by line; only lines our records or the brochure back (or wording the agent vouches for)
 *  can be kept, as the listing's highlights. */
export function AskAiPanel({ listing, onSaved }: { listing: Listing; onSaved: (l: Listing) => void }) {
  const [lang, setLang] = useState<DraftLanguage>('en')
  const prompts = useAsync(() => api.askAiPrompts(listing.id, lang), [listing.id, lang])
  const [shown, setShown] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)
  const [answer, setAnswer] = useState('')
  const [lines, setLines] = useState<AskAiLine[] | null>(null)
  const [picked, setPicked] = useState<Set<number>>(new Set())
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const have = listing.about?.highlights ?? []
  const room = MAX_HIGHLIGHTS - have.length

  async function open(p: AskAiPrompt, ai: (typeof AIS)[number]) {
    if (ai.copy) setNote((await copy(p.text)) ? `Prompt copied. Paste it in ${ai.name}.` : 'Copy the prompt below, then paste it in Gemini.')
    else setNote(`Opened ${ai.name}. Copy its answer and paste it below.`)
    window.open(ai.url(p.text), '_blank', 'noopener')
  }

  async function check() {
    setBusy(true)
    setErr(null)
    try {
      setLines(await api.askAiCheck(listing.id, answer))
      setPicked(new Set())
    } catch (e) {
      setErr(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function saveHighlights(highlights: string[], done: string) {
    setBusy(true)
    setErr(null)
    try {
      onSaved(await api.updateListing(listing.id, { about: { ...(listing.about ?? {}), highlights } }))
      setPicked(new Set())
      setNote(done)
    } catch (e) {
      setErr(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const keep = () => {
    const add = [...picked].map((i) => lines?.[i]?.keep ?? '').filter((x) => x && !have.includes(x))
    return saveHighlights([...have, ...add].slice(0, MAX_HIGHLIGHTS), `Added ${Math.min(add.length, room)} to the listing's highlights.`)
  }

  return (
    <div className="space-y-4">
      <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" aria-label="Prompts">
        <p className="font-semibold">1. Ask your AI</p>
        <p className="text-sm text-gray-600">Our prompts carry this listing&apos;s facts and our rules. They open in your own ChatGPT or Claude account; for Gemini the prompt is copied for you to paste.</p>
        <div className="flex items-center gap-2 text-sm" role="group" aria-label="Answer language">
          {LANGS.map(([l, label]) => (
            <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)}
              className={`min-h-[44px] flex-1 rounded-lg font-semibold ${lang === l ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>{label}</button>
          ))}
        </div>
        {prompts.loading && !prompts.data && <Spinner />}
        {prompts.error && <ErrorBox message={prompts.error} onRetry={prompts.reload} />}
        {prompts.data?.map((p) => (
          <div key={p.id} className="space-y-2 rounded-xl border border-gray-100 bg-gray-50 p-3">
            <p className="font-semibold">{p.title}</p>
            <p className="text-sm text-gray-600">{p.use}</p>
            <div className="flex flex-wrap gap-2">
              {AIS.map((ai) => (
                <button key={ai.name} type="button" onClick={() => void open(p, ai)}
                  className="min-h-[44px] rounded-lg border border-blue-200 bg-white px-3 text-sm font-semibold text-blue-700 active:bg-blue-50">
                  {ai.copy ? `Copy & open ${ai.name}` : `Open in ${ai.name}`}
                </button>
              ))}
              <button type="button" onClick={async () => setNote((await copy(p.text)) ? 'Prompt copied.' : 'Could not copy: select the prompt text instead.')}
                className="min-h-[44px] rounded-lg px-3 text-sm font-semibold text-gray-700 active:bg-gray-100">Copy</button>
              <button type="button" onClick={() => setShown(shown === p.id ? null : p.id)} aria-expanded={shown === p.id}
                className="min-h-[44px] rounded-lg px-3 text-sm font-semibold text-gray-700 underline">{shown === p.id ? 'Hide prompt' : 'See prompt'}</button>
            </div>
            {shown === p.id && <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-white p-3 text-xs text-gray-800">{p.text}</pre>}
          </div>
        ))}
        {note && <p role="status" className="rounded-xl bg-blue-50 p-3 text-sm font-semibold text-blue-900">{note}</p>}
      </section>

      <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" aria-label="Check the answer">
        <p className="font-semibold">2. Paste the answer to check it</p>
        <p className="text-sm text-gray-600">Every number is looked up in MahaRERA, your listing and the builder&apos;s brochure. Lines with a number we cannot find cannot be kept.</p>
        <textarea value={answer} onChange={(e) => setAnswer(e.target.value)} rows={8} maxLength={20000}
          placeholder="Paste the AI's answer here" aria-label="The AI's answer"
          className="w-full rounded-xl border border-gray-300 p-3 text-sm" />
        <Btn disabled={busy || !answer.trim()} onClick={check}>{busy && !lines ? 'Checking…' : 'Check'}</Btn>
        {err && <ErrorBox message={err} />}
        {lines && lines.length === 0 && <p className="text-sm text-gray-600">No lines to check. Paste the answer with one point per line.</p>}
        {lines && lines.length > 0 && (
          <>
            <ul className="space-y-2">
              {lines.map((l, i) => {
                const s = STATUS[l.status]
                const can = !!l.keep && !have.includes(l.keep)
                return (
                  <li key={i} className="rounded-xl border border-gray-100 p-3">
                    <label className="flex gap-3">
                      <input type="checkbox" className="mt-1 h-5 w-5 shrink-0" disabled={!can}
                        checked={picked.has(i)} aria-label={`Keep: ${l.text}`}
                        onChange={(e) => {
                          const next = new Set(picked)
                          if (e.target.checked) next.add(i)
                          else next.delete(i)
                          setPicked(next)
                        }} />
                      <span className="min-w-0 space-y-1">
                        <span className="block text-sm">{l.text}</span>
                        <span className="flex flex-wrap items-center gap-2">
                          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${s.cls}`}>{s.label(l)}</span>
                          {l.source && <span className="text-xs text-gray-500">AI&apos;s source: {l.source}</span>}
                          {!can && l.keep && <span className="text-xs text-gray-500">Already a highlight</span>}
                        </span>
                      </span>
                    </label>
                  </li>
                )
              })}
            </ul>
            <p className="text-sm text-gray-600">
              {room > 0 ? `Highlights show on your listing page and the chat answers buyers with them. Room for ${room} more.`
                : `The listing already has ${MAX_HIGHLIGHTS} highlights. Remove one below to add another.`}
            </p>
            <Btn disabled={busy || picked.size === 0 || room <= 0} onClick={keep}>
              {picked.size > room ? `Add the first ${room} to highlights` : `Add ${picked.size || ''} to highlights`.replace('  ', ' ')}
            </Btn>
          </>
        )}
      </section>

      {have.length > 0 && (
        <section className="space-y-2 rounded-2xl border border-gray-200 bg-white p-4" aria-label="Highlights">
          <p className="font-semibold">Highlights on this listing</p>
          <ul className="space-y-2">
            {have.map((h) => (
              <li key={h} className="flex items-start gap-2 text-sm">
                <span className="min-w-0 flex-1">{h}</span>
                <button type="button" disabled={busy} onClick={() => void saveHighlights(have.filter((x) => x !== h), 'Highlight removed.')}
                  className="min-h-[44px] shrink-0 px-2 font-semibold text-red-600 underline">Remove</button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
