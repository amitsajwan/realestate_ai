'use client'
import React, { useCallback, useEffect, useId, useRef, useState } from 'react'
import { BROCHURE_MAX_BYTES, brochureApi, isReraNo, needsRegistrationAnswer, normaliseReraNo, pendingFacts } from '@/lib/app/brochure'
import type { BrochureApi, BrochureFact, BrochureKit, FactValue } from '@/lib/app/brochure'
import { t } from '@/lib/app/strings'
import { useBrochure } from '@/lib/app/useBrochure'
import { Btn, ErrorBox, inputCls } from './ui'

const isList = (v: FactValue): v is string[] => Array.isArray(v)
const isText = (v: FactValue): v is string | number => typeof v === 'string' || typeof v === 'number'

function valueText(v: FactValue): string {
  if (v === null || v === undefined) return ''
  if (isList(v)) return v.join(', ')
  if (typeof v === 'object') return Object.entries(v).map(([k, x]) => `${k}: ${String(x)}`).join(', ')
  return String(v)
}

/** Page thumbnail; the image is fetched with the agent's token. Tapping opens it large. */
function PageThumb({ listingId, page, client, onOpen }: { listingId: string; page: number; client: BrochureApi; onOpen: (src: string) => void }) {
  const [src, setSrc] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    let on = true
    client.pageImage(listingId, page).then((u) => on && setSrc(u), () => on && setFailed(true))
    return () => {
      on = false
    }
  }, [client, listingId, page])
  const label = `${t('brochureEnlarge')} ${page}`
  return (
    <button type="button" onClick={() => src && onOpen(src)} disabled={!src} aria-label={label}
      className="flex h-24 w-[4.5rem] shrink-0 items-center justify-center overflow-hidden rounded-lg border border-gray-200 bg-gray-50 text-xs text-gray-500">
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" className="h-full w-full object-cover" />
      ) : (
        <span>{failed ? `${t('brochurePage')} ${page}` : '...'}</span>
      )}
    </button>
  )
}

/** Full-screen page view. Escape or Close returns focus to the page. */
function PageViewer({ src, page, onClose }: { src: string; page: number; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    const back = document.activeElement as HTMLElement | null
    closeRef.current?.focus()
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      back?.focus?.()
    }
  }, [onClose])
  return (
    <div role="dialog" aria-modal="true" aria-label={`${t('brochurePage')} ${page}`} className="fixed inset-0 z-50 flex flex-col bg-black/90 p-3"
      onClick={onClose} data-testid="page-viewer">
      <div className="flex justify-end">
        <button ref={closeRef} type="button" onClick={onClose} className="min-h-[44px] rounded-xl bg-white px-4 text-base font-semibold text-gray-900">
          {t('brochureClose')}
        </button>
      </div>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={`${t('brochurePage')} ${page}`} className="mx-auto mt-3 max-h-full max-w-full flex-1 object-contain"
        onClick={(e) => e.stopPropagation()} />
    </div>
  )
}

/** Fix a fact: one text box for text and numbers; chips with remove and add for lists. */
function FactEditor({ fact, onSave, onCancel, busy }: {
  fact: BrochureFact
  onSave: (v: FactValue) => void
  onCancel: () => void
  busy: boolean
}) {
  const id = useId()
  const [text, setText] = useState(isText(fact.value) ? String(fact.value) : valueText(fact.value))
  const [items, setItems] = useState<string[]>(isList(fact.value) ? fact.value : [])
  const [draft, setDraft] = useState('')
  const list = isList(fact.value)
  const add = () => {
    const v = draft.trim()
    if (v && !items.includes(v)) setItems([...items, v])
    setDraft('')
  }
  const save = () => {
    if (list) return onSave(items)
    const v = text.trim()
    if (!v) return
    onSave(typeof fact.value === 'number' && /^-?\d+(\.\d+)?$/.test(v) ? Number(v) : v)
  }
  return (
    <div className="mt-2 space-y-2">
      {list ? (
        <>
          <ul className="flex list-none flex-wrap gap-2 p-0" aria-label={fact.label}>
            {items.map((it) => (
              <li key={it} className="flex items-center gap-1 rounded-full bg-blue-50 py-1 pl-3 pr-1 text-sm text-blue-900">
                {it}
                <button type="button" onClick={() => setItems(items.filter((x) => x !== it))} aria-label={`${t('brochureRemoveItem')} ${it}`}
                  className="flex h-8 w-8 items-center justify-center rounded-full text-blue-900 active:bg-blue-100">
                  <span aria-hidden>×</span>
                </button>
              </li>
            ))}
          </ul>
          <div className="flex gap-2">
            <label htmlFor={`${id}-add`} className="sr-only">{`${t('brochureAddItem')}: ${fact.label}`}</label>
            <input id={`${id}-add`} value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={80}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); add() } }} className={inputCls} />
            <Btn variant="secondary" block={false} onClick={add} disabled={!draft.trim()}>{t('brochureAddItem')}</Btn>
          </div>
        </>
      ) : (
        <>
          <label htmlFor={`${id}-text`} className="sr-only">{fact.label}</label>
          <input id={`${id}-text`} value={text} onChange={(e) => setText(e.target.value)} maxLength={300}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); save() } }} className={inputCls} />
        </>
      )}
      <div className="grid grid-cols-2 gap-2">
        <Btn onClick={save} disabled={busy || (list ? items.length === 0 : !text.trim())}>{t('brochureSave')}</Btn>
        <Btn variant="ghost" onClick={onCancel}>{t('brochureCancel')}</Btn>
      </div>
    </div>
  )
}

function FactRow({ fact, listingId, client, busy, onSet, onView }: {
  fact: BrochureFact
  listingId: string
  client: BrochureApi
  busy: boolean
  onSet: (state: BrochureFact['state'], value?: FactValue) => Promise<boolean>
  onView: (page: number, src: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const editable = isText(fact.value) || isList(fact.value)
  const dropped = fact.state === 'dropped'
  const tone = fact.state === 'confirmed' ? 'border-emerald-300 bg-emerald-50/40' : dropped ? 'border-gray-200 bg-gray-50' : 'border-gray-200 bg-white'
  const headingId = `fact-${fact.id}`
  return (
    <li className={`rounded-xl border p-3 ${tone}`} aria-labelledby={headingId} data-testid={`fact-${fact.id}`} data-state={fact.state}>
      <div className="flex gap-3">
        <PageThumb listingId={listingId} page={fact.page} client={client} onOpen={(src) => onView(fact.page, src)} />
        <div className="min-w-0 flex-1">
          <p id={headingId} className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            {fact.label}
            {fact.edited && <span className="ml-2 normal-case tracking-normal text-blue-700">· {t('brochureEdited')}</span>}
          </p>
          {isList(fact.value) ? (
            <ul className={`mt-1 flex list-none flex-wrap gap-1.5 p-0 ${dropped ? 'opacity-60' : ''}`}>
              {fact.value.map((it) => (
                <li key={it} className="rounded-full bg-gray-100 px-2.5 py-1 text-sm text-gray-800">{it}</li>
              ))}
            </ul>
          ) : (
            <p className={`mt-1 break-words text-base font-semibold text-gray-900 ${dropped ? 'line-through opacity-60' : ''}`}>{valueText(fact.value)}</p>
          )}
          <blockquote className="mt-1 break-words border-l-2 border-gray-300 pl-2 text-xs italic text-gray-600">
            <span className="sr-only">{t('brochureQuote')}, {t('brochurePage').toLowerCase()} {fact.page}: </span>
            &ldquo;{fact.quote}&rdquo; <span className="not-italic text-gray-500">({t('brochurePage').toLowerCase()} {fact.page})</span>
          </blockquote>
        </div>
      </div>
      {editing ? (
        <FactEditor fact={fact} busy={busy} onCancel={() => setEditing(false)}
          onSave={async (v) => { if (await onSet('confirmed', v)) setEditing(false) }} />
      ) : (
        <div className={`mt-2 grid gap-2 ${editable ? 'grid-cols-3' : 'grid-cols-2'}`} role="group" aria-label={fact.label}>
          <button type="button" aria-pressed={fact.state === 'confirmed'} disabled={busy}
            onClick={() => onSet(fact.state === 'confirmed' ? 'pending' : 'confirmed')}
            className={`min-h-[44px] rounded-xl border text-sm font-semibold disabled:opacity-60 ${fact.state === 'confirmed' ? 'border-emerald-600 bg-emerald-600 text-white' : 'border-emerald-300 bg-white text-emerald-800'}`}>
            {fact.state === 'confirmed' ? `✓ ${t('brochureConfirm')}` : t('brochureConfirm')}
          </button>
          <button type="button" aria-pressed={dropped} disabled={busy}
            onClick={() => onSet(dropped ? 'pending' : 'dropped')}
            className={`min-h-[44px] rounded-xl border text-sm font-semibold disabled:opacity-60 ${dropped ? 'border-gray-700 bg-gray-700 text-white' : 'border-gray-300 bg-white text-gray-700'}`}>
            {t('brochureDrop')}
          </button>
          {editable && (
            <button type="button" disabled={busy} onClick={() => setEditing(true)}
              className="min-h-[44px] rounded-xl border border-blue-200 bg-white text-sm font-semibold text-blue-700 disabled:opacity-60">
              {t('brochureFix')}
            </button>
          )}
        </div>
      )}
    </li>
  )
}

/** "Registered, or exempt?" Asked when MahaRERA has no record we could check; the answer is kept on the listing. */
function RegistrationBlock({ kit, busy, onAnswer }: {
  kit: BrochureKit
  busy: boolean
  onAnswer: (a: { status: 'registered'; rera_no: string } | { status: 'exempt' }) => Promise<boolean>
}) {
  const reg = kit.registration
  const ask = needsRegistrationAnswer(kit)
  const [changing, setChanging] = useState(false)
  const [choice, setChoice] = useState<'registered' | 'exempt' | null>(reg.rera_no ? 'registered' : null)
  const [rera, setRera] = useState(reg.rera_no ?? '')
  const [touched, setTouched] = useState(false)
  const id = useId()
  const reraBad = choice === 'registered' && !isReraNo(rera)

  if (!ask && !changing) {
    if (reg.status === 'verified') {
      return (
        <p className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-900" data-testid="reg-status">
          {t('regVerified')}{reg.rera_no ? ` ${reg.rera_no}` : ''}
        </p>
      )
    }
    return (
      <div className="flex items-center justify-between gap-2 rounded-xl bg-gray-50 p-3 text-sm text-gray-800" data-testid="reg-status">
        <p>{reg.status === 'exempt' ? t('regIsExempt') : `${t('regByAgent')}: ${reg.rera_no ?? ''}`}</p>
        <button type="button" onClick={() => setChanging(true)} className="min-h-[44px] px-2 font-semibold text-blue-700 underline">{t('regChange')}</button>
      </div>
    )
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setTouched(true)
    if (!choice || reraBad) return
    const ok = await onAnswer(choice === 'registered' ? { status: 'registered', rera_no: normaliseReraNo(rera) } : { status: 'exempt' })
    if (ok) setChanging(false)
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded-xl border border-amber-300 bg-amber-50 p-3" aria-labelledby={`${id}-q`} data-testid="reg-question">
      <fieldset className="space-y-2">
        <legend id={`${id}-q`} className="text-base font-semibold text-gray-900">{t('regQuestion')}</legend>
        {reg.note && <p className="text-sm text-gray-700">{reg.note}</p>}
        <p id={`${id}-hint`} className="text-xs text-gray-700">{t('regHint')}</p>
        {(['registered', 'exempt'] as const).map((c) => (
          <label key={c} className={`flex min-h-[48px] cursor-pointer items-center gap-3 rounded-xl border bg-white px-3 text-sm font-semibold ${choice === c ? 'border-blue-600 text-blue-900' : 'border-gray-300 text-gray-800'}`}>
            <input type="radio" name={`${id}-reg`} value={c} checked={choice === c} onChange={() => setChoice(c)} aria-describedby={`${id}-hint`}
              className="h-5 w-5 accent-blue-600" />
            {c === 'registered' ? t('regRegistered') : t('regExempt')}
          </label>
        ))}
      </fieldset>
      {choice === 'registered' && (
        <div className="space-y-1">
          <label htmlFor={`${id}-rera`} className="block text-sm font-semibold text-gray-800">{t('regNumber')}</label>
          <input id={`${id}-rera`} value={rera} onChange={(e) => setRera(e.target.value)} onBlur={() => setTouched(true)}
            autoCapitalize="characters" autoComplete="off" spellCheck={false} inputMode="text" placeholder="P5..." maxLength={20}
            aria-invalid={touched && reraBad} aria-describedby={`${id}-rera-hint`} className={inputCls} />
          <p id={`${id}-rera-hint`} className={`text-xs ${touched && reraBad ? 'text-red-700' : 'text-gray-600'}`} role={touched && reraBad ? 'alert' : undefined}>
            {touched && reraBad ? t('regNumberInvalid') : t('regNumberHint')}
          </p>
        </div>
      )}
      <div className={changing ? 'grid grid-cols-2 gap-2' : ''}>
        <Btn type="submit" disabled={busy || !choice}>{t('regSave')}</Btn>
        {changing && <Btn variant="ghost" onClick={() => setChanging(false)}>{t('brochureCancel')}</Btn>}
      </div>
    </form>
  )
}

/**
 * The listing's brochure: upload a PDF, then "Confirm the kit" (each fact with its page and the exact words, one tap to confirm or
 * drop) and the MahaRERA registration question when there is no record to check against.
 */
export function BrochureCard({ listingId, client = brochureApi }: { listingId: string; client?: BrochureApi }) {
  const b = useBrochure(listingId, client)
  const fileRef = useRef<HTMLInputElement>(null)
  const [view, setView] = useState<{ page: number; src: string } | null>(null)
  const closeView = useCallback(() => setView(null), [])
  const inputId = useId()
  const { kit } = b
  const uploading = b.phase !== 'idle'
  const pending = pendingFacts(kit)
  const imageOnly = kit?.image_only_pages.length ?? 0

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    e.target.value = '' // the same file can be chosen again after an error
    if (f) await b.upload(f)
  }

  return (
    <section aria-labelledby="brochure-title" className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" data-testid="brochure-card">
      <h2 id="brochure-title" className="text-lg font-bold text-gray-900">{t('brochureTitle')}</h2>

      {!kit && !b.loading && <p className="text-sm text-gray-600">{t('brochureHelp')}</p>}

      <input ref={fileRef} id={inputId} type="file" accept="application/pdf,.pdf" className="sr-only" tabIndex={-1} aria-hidden
        onChange={onFile} data-testid="brochure-file" data-max-bytes={BROCHURE_MAX_BYTES} />

      {uploading ? (
        <div role="status" aria-live="polite" className="space-y-2 rounded-xl bg-blue-50 p-3 text-sm text-blue-900" data-testid="brochure-progress">
          {b.phase === 'uploading' ? (
            <>
              <p>{t('brochureUploading')} {Math.round(b.progress * 100)}%</p>
              <div className="h-2 w-full overflow-hidden rounded-full bg-blue-100">
                <div className="h-full rounded-full bg-blue-600 transition-[width]" style={{ width: `${Math.round(b.progress * 100)}%` }} />
              </div>
              <progress className="sr-only" max={100} value={Math.round(b.progress * 100)} aria-label={t('brochureUploading')} />
            </>
          ) : (
            <p className="flex items-center gap-3">
              <span aria-hidden className="h-5 w-5 flex-none animate-spin rounded-full border-2 border-blue-200 border-t-blue-600" />
              {t('brochureReading')}
            </p>
          )}
        </div>
      ) : (
        !b.loading && (
          <div className="space-y-1">
            <Btn variant={kit ? 'secondary' : 'primary'} onClick={() => fileRef.current?.click()}>
              {kit ? t('brochureReplace') : t('brochureChoose')}
            </Btn>
            <p className="text-center text-xs text-gray-500">{t('brochureLimits')}</p>
          </div>
        )
      )}

      {b.error && <ErrorBox message={b.error} />}

      {kit && kit.status === 'failed' && <ErrorBox message={`${t('brochureFailed')}${kit.error ? ` ${kit.error}` : ''}`} />}

      {kit && kit.status === 'done' && (
        <div className="space-y-3" data-testid="brochure-kit">
          <div className="flex items-baseline justify-between gap-2">
            <h3 className="text-base font-bold text-gray-900">{t('brochureConfirmTitle')}</h3>
            <span className="truncate text-xs text-gray-500" title={kit.filename}>{kit.filename} · {kit.pages}p</span>
          </div>
          <p className="text-sm text-gray-700">{t('brochureAttribution')}</p>
          {imageOnly > 0 && (
            <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900" data-testid="image-only">
              {imageOnly} {imageOnly === 1 ? t('brochureImagePagesOne') : t('brochureImagePagesMany')}
            </p>
          )}

          <RegistrationBlock key={`${kit.registration.status}:${kit.registration.rera_no ?? ''}`} kit={kit} busy={!!b.saving.registration} onAnswer={b.setRegistration} />

          {kit.facts.length === 0 ? (
            <p className="text-sm text-gray-600">{t('brochureNoFacts')}</p>
          ) : (
            <>
              <div className="flex items-center justify-between gap-2">
                <p role="status" className="text-sm text-gray-700">
                  {pending.length > 0 ? `${pending.length} ${t('brochurePending')}` : t('brochureAllChecked')}
                </p>
                {pending.length > 0 && (
                  <Btn block={false} className="!min-h-[44px] !px-4 !text-sm" onClick={() => void b.confirmAll()}
                    disabled={Object.values(b.saving).some(Boolean)}>
                    {t('brochureConfirmAll')} ({pending.length})
                  </Btn>
                )}
              </div>
              <ul className="list-none space-y-3 p-0">
                {kit.facts.map((f) => (
                  <FactRow key={f.id} fact={f} listingId={listingId} client={client} busy={!!b.saving[f.id]}
                    onSet={(state, value) => b.setFact(f.id, state, value)} onView={(page, src) => setView({ page, src })} />
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {view && <PageViewer src={view.src} page={view.page} onClose={closeView} />}
    </section>
  )
}
