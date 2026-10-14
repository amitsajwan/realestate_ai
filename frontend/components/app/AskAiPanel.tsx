'use client'
import React, { useState } from 'react'
import { Btn, ErrorBox, Spinner } from '@/components/app/ui'
import { api, errorMessage } from '@/lib/app/client'
import { compressImage } from '@/lib/app/imageCompress'
import { qualityFields } from '@/lib/app/quality'
import type { AskAiAnswer, AskAiPrompt, AskAiStatus, DraftLanguage, Listing, ListingInput, PictureSlot } from '@/lib/app/types'
import { useAsync } from '@/lib/app/useAsync'

const MAX_HIGHLIGHTS = 6 // listings/about.py

const LANGS: Array<[DraftLanguage, string]> = [['en', 'English'], ['mr', 'मराठी'], ['hi', 'हिन्दी']]

/** ChatGPT and Claude take the prompt in the link; Gemini does not, so its button copies the prompt first. */
const AIS: Array<{ name: string; url: (q: string) => string; copy?: boolean }> = [
  { name: 'ChatGPT', url: (q) => `https://chatgpt.com/?q=${encodeURIComponent(q)}` },
  { name: 'Claude', url: (q) => `https://claude.ai/new?q=${encodeURIComponent(q)}` },
  { name: 'Gemini', url: () => 'https://gemini.google.com/app', copy: true },
]

const CHIP: Record<AskAiStatus, { label: (missing: string[]) => string; cls: string }> = {
  checked: { label: () => 'Numbers checked', cls: 'bg-green-100 text-green-800' },
  unchecked: { label: (m) => `Not in our records: ${m.join(', ')}`, cls: 'bg-red-100 text-red-800' },
  words: { label: () => 'No numbers: check it is true', cls: 'bg-gray-100 text-gray-700' },
}

function Chip({ status, missing }: { status: AskAiStatus; missing: string[] }) {
  const c = CHIP[status]
  return <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${c.cls}`}>{c.label(missing)}</span>
}

async function copy(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

const card = 'space-y-3 rounded-2xl border border-gray-200 bg-white p-4'
const small = 'min-h-[44px] rounded-lg px-3 text-sm font-semibold'

/** The listing's media with the plan's photos first, in plan order. */
function mediaFor(listing: Listing, plan: PictureSlot[]): ListingInput['media'] {
  const planned = plan.map((s) => s.url).filter((u): u is string => !!u)
  const byUrl = new Map(listing.media.map((m) => [m.url, m]))
  const first = planned.map((url) => byUrl.get(url) ?? { url, kind: 'image' as const, order: 0 })
  const rest = listing.media.filter((m) => !planned.includes(m.url))
  return [...first, ...rest].map((m, order) => ({ ...m, order }))
}

/** Ask AI: the agent's own ChatGPT, Claude or Gemini, used by hand. One step at a time: open that step's prompt in your AI,
 *  paste its answer back, Studio reads it in parts and checks every number against our records. The team then finds a photo
 *  for each picture of the plan; checked lines can be kept as the listing's highlights. */
export function AskAiPanel({ listing, onSaved }: { listing: Listing; onSaved: (l: Listing) => void }) {
  const [lang, setLang] = useState<DraftLanguage>('en')
  const prompts = useAsync(() => api.askAiPrompts(listing.id, lang), [listing.id, lang])
  const [active, setActive] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [answers, setAnswers] = useState<Record<string, AskAiAnswer | null>>({})
  const [picked, setPicked] = useState<Set<number>>(new Set())
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const have = listing.about?.highlights ?? []
  const room = MAX_HIGHLIGHTS - have.length
  const plan = listing.picture_plan ?? []
  const list = prompts.data ?? []
  const openId = active && list.some((p) => p.id === active) ? active : (list[0]?.id ?? null)

  async function open(p: AskAiPrompt, ai: (typeof AIS)[number]) {
    if (ai.copy) setNote((await copy(p.text)) ? `Prompt copied. Paste it in ${ai.name}, then bring its whole answer back here.` : 'Copy the prompt below, then paste it in Gemini.')
    else setNote(`Opened ${ai.name}. When it answers, copy the whole answer and paste it below.`)
    window.open(ai.url(p.text), '_blank', 'noopener')
  }

  async function save(patch: ListingInput, done: string) {
    setBusy(true)
    setErr(null)
    try {
      onSaved(await api.updateListing(listing.id, patch))
      setNote(done)
      return true
    } catch (e) {
      setErr(errorMessage(e))
      return false
    } finally {
      setBusy(false)
    }
  }

  async function check(p: AskAiPrompt) {
    setBusy(true)
    setErr(null)
    try {
      const read = await api.askAiCheck(listing.id, drafts[p.id] ?? '')
      setAnswers((a) => ({ ...a, [p.id]: read }))
      setPicked(new Set())
    } catch (e) {
      setErr(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const keepLines = (answer: AskAiAnswer) => {
    const add = [...picked].map((i) => answer.lines[i]?.keep ?? '').filter((x) => x && !have.includes(x))
    void save({ about: { ...(listing.about ?? {}), highlights: [...have, ...add].slice(0, MAX_HIGHLIGHTS) } },
      `Added ${Math.min(add.length, room)} to the listing's highlights.`).then((ok) => ok && setPicked(new Set()))
  }

  const usePlan = (answer: AskAiAnswer) => {
    // a slot keeps the photo already found for the same kind of picture at the same place
    const next = answer.pictures.map(({ status: _s, missing: _m, ...slot }, i) => ({ ...slot, url: plan[i]?.type === slot.type ? plan[i].url ?? null : null }))
    void save({ picture_plan: next, media: mediaFor(listing, next) }, 'Picture plan saved. Now add a photo for each picture below.')
  }

  async function fillSlot(i: number, file: File | null) {
    const next = plan.map((s) => ({ ...s }))
    let media = listing.media
    if (file) {
      setBusy(true)
      setErr(null)
      try {
        const [up] = await api.uploadImages([await compressImage(file)])
        next[i].url = up.url
        media = [...media, { url: up.url, kind: 'image' as const, order: media.length, ...qualityFields(up) }]
      } catch (e) {
        setErr(errorMessage(e))
        setBusy(false)
        return
      }
    } else {
      media = media.filter((m) => m.url !== next[i].url)
      next[i].url = null
    }
    await save({ picture_plan: next, media: mediaFor({ ...listing, media }, next) }, file ? `Photo added for picture ${i + 1}.` : `Photo removed from picture ${i + 1}.`)
  }

  return (
    <div className="space-y-4">
      <section className={card} aria-label="Ask your AI">
        <p className="font-semibold">Ask your AI, one step at a time</p>
        <p className="text-sm text-gray-600">Each step is one prompt that carries this listing&apos;s checked facts and our rules, and asks the AI to think
          before it answers. Open it in your own ChatGPT, Claude or Gemini, then paste what it says back into that step.</p>
        <div className="flex items-center gap-2 text-sm" role="group" aria-label="Language of the posts">
          {LANGS.map(([l, label]) => (
            <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)}
              className={`min-h-[44px] flex-1 rounded-lg font-semibold ${lang === l ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>{label}</button>
          ))}
        </div>
        {prompts.loading && !prompts.data && <Spinner />}
        {prompts.error && <ErrorBox message={prompts.error} onRetry={prompts.reload} />}
        <ol className="space-y-2">
          {list.map((p, i) => (
            <Step key={p.id} p={p} n={i + 1} nextTitle={list[i + 1]?.title} open={openId === p.id}
              done={!!answers[p.id]} busy={busy} err={openId === p.id ? err : null} note={openId === p.id ? note : null}
              text={drafts[p.id] ?? ''} answer={answers[p.id] ?? null} picked={picked} setPicked={setPicked}
              have={have} room={room} hasPlan={plan.length > 0}
              onToggle={() => { setActive(openId === p.id ? null : p.id); setPicked(new Set()) }}
              onOpenAI={(ai) => void open(p, ai)}
              onCopyPrompt={async () => setNote((await copy(p.text)) ? 'Prompt copied. Paste it in your AI.' : 'Could not copy: select the prompt text instead.')}
              onText={(t) => setDrafts((d) => ({ ...d, [p.id]: t }))}
              onCheck={() => void check(p)}
              onKeep={() => keepLines(answers[p.id]!)}
              onUsePlan={() => answers[p.id] && usePlan(answers[p.id]!)}
              onCopyAnswer={async (t) => setNote((await copy(t)) ? 'Copied.' : 'Could not copy.')}
              onNext={() => { setActive(list[i + 1]?.id ?? null); setNote(null); setErr(null) }}
            />
          ))}
        </ol>
      </section>

      {plan.length > 0 && (
        <section className={card} aria-label="Picture plan">
          <p className="font-semibold">Picture plan: find a photo for each</p>
          <p className="text-sm text-gray-600">Use only pictures the builder allows agents to use. Your posts and reels use these photos; for now marketing picks their order by photo quality.</p>
          <ol className="space-y-3">
            {plan.map((s, i) => (
              <li key={i} className="space-y-2 rounded-xl border border-gray-100 p-3">
                <p className="text-sm"><span className="font-semibold">{i + 1}. {s.type}</span>: {s.shows}</p>
                {s.where && <p className="text-xs text-gray-600">Where to find it: {s.where}</p>}
                {s.text && <p className="text-xs text-gray-600">Text on it: “{s.text}”</p>}
                {s.url ? (
                  <div className="flex items-center gap-3">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={s.url} alt={s.shows} className="h-20 w-20 rounded-lg object-cover" />
                    <button type="button" disabled={busy} onClick={() => void fillSlot(i, null)} className={`${small} text-red-600 underline`}>Remove photo</button>
                  </div>
                ) : (
                  <label className={`${small} inline-flex cursor-pointer items-center border border-blue-200 bg-white text-blue-700`}>
                    Add photo
                    <input type="file" accept="image/*" className="sr-only" disabled={busy}
                      onChange={(e) => { const f = e.target.files?.[0] ?? null; e.target.value = ''; if (f) void fillSlot(i, f) }} />
                  </label>
                )}
              </li>
            ))}
          </ol>
          <p className="text-sm text-gray-600">{plan.filter((s) => s.url).length} of {plan.length} pictures found.</p>
        </section>
      )}

      {have.length > 0 && (
        <section className={card} aria-label="Highlights">
          <p className="font-semibold">Highlights on this listing</p>
          <ul className="space-y-2">
            {have.map((h) => (
              <li key={h} className="flex items-start gap-2 text-sm">
                <span className="min-w-0 flex-1">{h}</span>
                <button type="button" disabled={busy}
                  onClick={() => void save({ about: { ...(listing.about ?? {}), highlights: have.filter((x) => x !== h) } }, 'Highlight removed.')}
                  className={`${small} shrink-0 text-red-600 underline`}>Remove</button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

/** One Ask AI step, closed except the one being used: open the prompt in your AI, paste its answer, read what it suggests. */
function Step({ p, n, nextTitle, open, done, busy, err, note, text, answer, picked, setPicked, have, room, onToggle,
  onOpenAI, onCopyPrompt, onText, onCheck, onKeep, onUsePlan, hasPlan, onCopyAnswer, onNext }: {
  p: AskAiPrompt; n: number; nextTitle?: string; open: boolean; done: boolean; busy: boolean
  err: string | null; note: string | null; text: string; answer: AskAiAnswer | null; picked: Set<number>
  setPicked: (s: Set<number>) => void; have: string[]; room: number
  onToggle: () => void; onOpenAI: (ai: (typeof AIS)[number]) => void; onCopyPrompt: () => void
  onText: (t: string) => void; onCheck: () => void; onKeep: () => void; onUsePlan: () => void; hasPlan: boolean
  onCopyAnswer: (t: string) => void; onNext: () => void
}) {
  const [showPrompt, setShowPrompt] = useState(false)
  const best = p.best ? AIS.find((a) => a.name === p.best) : undefined
  const rest = AIS.filter((a) => a !== best)
  return (
    <li className={`rounded-xl border ${open ? 'border-blue-200 bg-white' : 'border-gray-200 bg-gray-50'}`}>
      <h3>
        <button type="button" aria-expanded={open} aria-controls={`step-${p.id}`} onClick={onToggle}
          className="flex min-h-[44px] w-full items-start gap-3 p-3 text-left">
          <span aria-hidden className={`grid h-7 w-7 shrink-0 place-items-center rounded-full text-sm font-bold ${done ? 'bg-green-600 text-white' : open ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}>
            {done ? '✓' : n}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block font-semibold">{p.title}</span>
            <span className="block text-sm text-gray-600">{p.use}</span>
            {p.hint && <span className="mt-1 block w-fit rounded-lg bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800">{p.hint}</span>}
          </span>
          <span aria-hidden className="shrink-0 text-gray-500">{open ? '▴' : '▾'}</span>
        </button>
      </h3>
      {open && (
        <div id={`step-${p.id}`} className="space-y-4 border-t border-gray-100 p-3">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase text-gray-500">a. Open it in your AI</p>
            {best && (
              <button type="button" onClick={() => onOpenAI(best)}
                className="min-h-[48px] w-full rounded-xl bg-blue-600 px-4 text-left text-white active:bg-blue-700">
                <span className="block font-semibold">Open in {best.name}</span>
                {p.best_note && <span className="block text-xs text-blue-100">works best with {p.best_note}</span>}
              </button>
            )}
            <div className="flex flex-wrap gap-2">
              {!best && AIS.map((ai) => (
                <button key={ai.name} type="button" onClick={() => onOpenAI(ai)} className={`${small} border border-blue-200 bg-white text-blue-700 active:bg-blue-50`}>
                  {ai.copy ? `Copy & open ${ai.name}` : `Open in ${ai.name}`}
                </button>
              ))}
              {best && rest.map((ai) => (
                <button key={ai.name} type="button" onClick={() => onOpenAI(ai)} className={`${small} text-gray-700 active:bg-gray-100`}>
                  {ai.copy ? `Copy & open ${ai.name}` : `or ${ai.name}`}
                </button>
              ))}
              <button type="button" onClick={onCopyPrompt} className={`${small} text-gray-700 active:bg-gray-100`}>Copy the prompt</button>
              <button type="button" onClick={() => setShowPrompt((s) => !s)} aria-expanded={showPrompt}
                className={`${small} text-gray-700 underline`}>{showPrompt ? 'Hide the prompt' : 'See the exact prompt'}</button>
            </div>
            {showPrompt && <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-gray-50 p-3 text-xs text-gray-800">{p.text}</pre>}
          </div>
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase text-gray-500">b. Paste {p.paste ?? 'the whole answer'}</p>
            <textarea value={text} onChange={(e) => onText(e.target.value)} rows={6} maxLength={20000}
              placeholder="Paste your AI's answer here, with its headings" aria-label={`The answer to ${p.title}`}
              className="w-full rounded-xl border border-gray-300 p-3 text-sm" />
            <Btn disabled={busy || !text.trim()} onClick={onCheck}>{busy ? 'Checking…' : answer ? 'Check again' : 'Check the answer'}</Btn>
            {err && <ErrorBox message={err} />}
            {note && <p role="status" className="rounded-xl bg-blue-50 p-3 text-sm font-semibold text-blue-900">{note}</p>}
            {p.after && <p className="text-sm text-gray-600">{p.after}</p>}
          </div>
          {answer && (
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase text-gray-500">c. What it suggests</p>
              <AnswerView answer={answer} picked={picked} setPicked={setPicked} have={have} room={room} busy={busy}
                onKeep={onKeep} onUsePlan={onUsePlan} hasPlan={hasPlan} onCopy={onCopyAnswer} />
              {nextTitle && <button type="button" onClick={onNext} className={`${small} font-semibold text-blue-700 underline`}>Next step: {nextTitle}</button>}
            </div>
          )}
        </div>
      )}
    </li>
  )
}

function AnswerView({ answer, picked, setPicked, have, room, busy, onKeep, onUsePlan, hasPlan, onCopy }: {
  answer: AskAiAnswer
  picked: Set<number>
  setPicked: (s: Set<number>) => void
  have: string[]
  room: number
  busy: boolean
  onKeep: () => void
  onUsePlan: () => void
  hasPlan: boolean
  onCopy: (text: string) => void
}) {
  const { lines, headline, captions, pictures, reel, missing } = answer
  const empty = !lines.length && !headline && !captions.length && !pictures.length && !reel.length && !missing.length
  if (empty) return <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">Nothing to read in this answer. Paste the whole answer, with its headings.</p>
  const copyBtn = (t: string) => <button type="button" onClick={() => onCopy(t)} className={`${small} shrink-0 text-blue-700 underline`}>Copy</button>
  return (
    <div className="space-y-4">

      {headline && (
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase text-gray-500">Headline</p>
          <div className="flex items-start gap-2"><p className="min-w-0 flex-1 font-semibold">{headline.text}</p>{copyBtn(headline.text)}</div>
          <Chip status={headline.status} missing={headline.missing} />
        </div>
      )}

      {pictures.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase text-gray-500">Pictures, in order</p>
          <ol className="space-y-2">
            {pictures.map((p, i) => (
              <li key={i} className="rounded-xl border border-gray-100 p-3 text-sm">
                <p><span className="font-semibold">{i + 1}. {p.type}</span>: {p.shows}</p>
                {p.where && <p className="text-xs text-gray-600">Where: {p.where}</p>}
                {p.text && <p className="text-xs text-gray-600">Text on it: “{p.text}”</p>}
                {p.status === 'unchecked' && <p className="mt-1"><Chip status={p.status} missing={p.missing} /> <span className="text-xs text-gray-600">(its text is dropped)</span></p>}
                {p.why && <p className="text-xs text-gray-500">Why: {p.why}</p>}
              </li>
            ))}
          </ol>
          <Btn disabled={busy} onClick={onUsePlan}>{hasPlan ? 'Use this picture plan instead' : 'Use this picture plan'}</Btn>
        </div>
      )}

      {captions.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase text-gray-500">Captions</p>
          {captions.map((c, i) => (
            <div key={i} className="space-y-1 rounded-xl border border-gray-100 p-3">
              <div className="flex items-start gap-2"><p className="min-w-0 flex-1 whitespace-pre-wrap text-sm">{c.text}</p>{c.status !== 'unchecked' && copyBtn(c.text)}</div>
              <Chip status={c.status} missing={c.missing} />
            </div>
          ))}
        </div>
      )}

      {reel.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase text-gray-500">Reel script</p>
          <ol className="space-y-1 text-sm">
            {reel.map((r, i) => (
              <li key={i}>
                <span className="font-semibold">{i + 1}. {r.picture}</span>: “{r.screen}”, says “{r.spoken}”{' '}
                {r.status === 'unchecked' && <Chip status={r.status} missing={r.missing} />}
              </li>
            ))}
          </ol>
          {reel.every((r) => r.status !== 'unchecked') && copyBtn(reel.map((r, i) => `${i + 1}. [${r.picture}] ${r.screen} / ${r.spoken}`).join('\n'))}
        </div>
      )}

      {missing.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase text-gray-500">Ask the builder</p>
          <ul className="list-disc pl-5 text-sm">{missing.map((m) => <li key={m}>{m}</li>)}</ul>
        </div>
      )}

      {lines.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase text-gray-500">Facts</p>
          <ul className="space-y-2">
            {lines.map((l, i) => {
              const can = !!l.keep && !have.includes(l.keep)
              return (
                <li key={i} className="rounded-xl border border-gray-100 p-3">
                  <label className="flex gap-3">
                    <input type="checkbox" className="mt-1 h-5 w-5 shrink-0" disabled={!can} checked={picked.has(i)} aria-label={`Keep: ${l.text}`}
                      onChange={(e) => {
                        const next = new Set(picked)
                        if (e.target.checked) next.add(i)
                        else next.delete(i)
                        setPicked(next)
                      }} />
                    <span className="min-w-0 space-y-1">
                      <span className="block text-sm">{l.text}</span>
                      <span className="flex flex-wrap items-center gap-2">
                        <Chip status={l.status} missing={l.missing} />
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
          <Btn disabled={busy || picked.size === 0 || room <= 0} onClick={onKeep}>
            {picked.size > room ? `Add the first ${room} to highlights` : `Add ${picked.size || ''} to highlights`.replace('  ', ' ')}
          </Btn>
        </div>
      )}
    </div>
  )
}
