'use client'
import React, { useEffect, useRef, useState } from 'react'
import { aboutSummaryLines } from '@/lib/app/about'
import { formatInr, groupIndian, parseInr } from '@/lib/app/format'
import { t } from '@/lib/app/strings'
import type { About, DraftSource, Furnishing, ListingInput, PropertyType, ReraCandidate, Transaction } from '@/lib/app/types'
import { LOW_CONFIDENCE, priceSanity } from '@/lib/app/validate'
import { ChipPicker } from './JoinFlow'
import { Field, inputCls } from './ui'

const TYPES: PropertyType[] = ['apartment', 'villa', 'house', 'plot', 'commercial', 'office', 'shop']
const AMENITIES = ['Parking', 'Lift', 'Gym', 'Swimming pool', 'Security', 'Power backup', 'Garden', 'Clubhouse']

export interface ReviewFormProps {
  value: ListingInput
  onChange: (v: ListingInput) => void
  confidence?: Record<string, number>
  /** Fields still missing (computed live by the caller). */
  missing?: string[]
  /** Server-side field errors (e.g. from a 422). */
  errors?: Record<string, string>
  /** Project and area info (kept outside `value` so the form stays the listing fields). Shows a summary with an edit link. */
  about?: About | null
  onEditAbout?: () => void
  /** Where each field came from (AI draft): shown as a small badge. */
  sources?: Record<string, DraftSource>
  /** MahaRERA matches for the project, offered as one-tap picks while there is no number. */
  reraCandidates?: ReraCandidate[]
  /** Shown on the price (and the price is focused) when it is the only thing left, e.g. the brochure had none. */
  priceHint?: string | null
}

const SOURCE_LABEL = { brochure: 'srcBrochure', maharera: 'srcMaharera', agent: 'srcAgent' } as const

function SourceBadge({ source }: { source?: DraftSource }) {
  if (!source || !SOURCE_LABEL[source]) return null
  const tone = source === 'brochure' ? 'bg-purple-100 text-purple-800' : source === 'maharera' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'
  return <span data-source={source} className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${tone}`}>{t(SOURCE_LABEL[source])}</span>
}

function ReraPicks({ candidates, onPick }: { candidates: ReraCandidate[]; onPick: (patch: ListingInput) => void }) {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null
  const chip = 'min-h-[44px] rounded-full border px-4 text-left text-sm font-semibold'
  return (
    <div className="mt-2 space-y-2" role="group" aria-label={t('reraIsItOne')} data-testid="rera-candidates">
      <p className="text-sm font-semibold text-gray-800">{t('reraIsItOne')}</p>
      <div className="flex flex-wrap gap-2">
        {candidates.map((c) => (
          <button key={c.regno} type="button" onClick={() => onPick({ rera_no: c.regno, rera_status: null })} className={`${chip} border-blue-600 bg-white text-blue-700`}>
            {c.name}, {c.regno}{c.taluka ? ` (${c.taluka})` : ''}
          </button>
        ))}
        <button type="button" onClick={() => setDismissed(true)} className={`${chip} border-gray-300 bg-white text-gray-700`}>{t('reraNoneOfThese')}</button>
        <button type="button" onClick={() => onPick({ rera_status: 'not_registered', rera_no: null })} className={`${chip} border-gray-300 bg-white text-gray-700`}>{t('reraNotRegistered')}</button>
      </div>
    </div>
  )
}

function PriceField({ value, onChange, flag, warning, hint, children }: { value?: number; onChange: (n: number) => void; flag: { error?: string; check?: boolean; required?: boolean }; warning?: string | null; hint?: string | null; children?: React.ReactNode }) {
  const [text, setText] = useState(value ? groupIndian(value) : '')
  const ref = useRef<HTMLInputElement>(null)
  const shown = !!hint && !value
  useEffect(() => {
    if (shown) ref.current?.focus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hint])
  // Keep the text in sync when the value is replaced from outside (e.g. draft arrives), but not while typing.
  const parsed = parseInr(text)
  useEffect(() => {
    if (value && parseInr(text) !== value) setText(groupIndian(value))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])
  return (
    <Field label="Price (₹)" htmlFor="price" {...flag}>
      {shown && <p role="status" data-testid="price-hint" className="mb-1 text-sm font-semibold text-red-700">{hint}</p>}
      <input
        ref={ref}
        id="price"
        className={`${inputCls} ${shown ? 'ring-2 ring-red-500' : ''}`}
        inputMode="text"
        placeholder="85 lakh, 1.2 cr or 8500000"
        value={text}
        onChange={(e) => {
          setText(e.target.value)
          const n = parseInr(e.target.value)
          if (n !== null) onChange(n)
        }}
      />
      <p className="mt-1 text-sm font-semibold text-blue-700">
        {parsed ? `₹${formatInr(parsed)}  (₹${groupIndian(parsed)})` : text ? "Can't read this. Try 85 lakh" : ''}
      </p>
      {warning && <p role="alert" className="mt-1 rounded-lg bg-amber-50 p-2 text-sm font-semibold text-amber-900">⚠ {warning}</p>}
      {children}
    </Field>
  )
}

function AboutSummary({ about, onEdit }: { about?: About | null; onEdit: () => void }) {
  const lines = aboutSummaryLines(about)
  return (
    <section aria-label={t('aboutSummaryTitle')} className="rounded-xl border border-gray-200 bg-white p-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-gray-800">{t('aboutSummaryTitle')}</h2>
        <button type="button" onClick={onEdit} className="min-h-[44px] min-w-[44px] text-sm font-semibold text-blue-700 underline">{lines.length ? t('aboutEdit') : t('aboutAdd')}</button>
      </div>
      {lines.length ? (
        <ul className="mt-1 space-y-1 text-sm text-gray-700">{lines.map((l) => <li key={l}>{l}</li>)}</ul>
      ) : (
        <p className="mt-1 text-sm text-gray-500">{t('aboutSummaryEmpty')}</p>
      )}
    </section>
  )
}

export function ReviewForm({ value, onChange, confidence = {}, missing = [], errors = {}, about, onEditAbout, sources = {}, reraCandidates = [], priceHint }: ReviewFormProps) {
  const src = (key: string) => <SourceBadge source={sources[key]} />
  const [lang, setLang] = useState<'en' | 'hi' | 'mr'>('en')
  const set = (patch: ListingInput) => onChange({ ...value, ...patch })
  const photos = (value.media ?? []).filter((m) => (m.kind ?? 'image') === 'image')
  const flag = (key: string) => {
    const req = missing.includes(key) || errors[key] === 'Required'
    const err = req ? 'Required' : errors[key]
    const check = !err && confidence[key] !== undefined && confidence[key] < LOW_CONFIDENCE
    return { error: err, required: req, check }
  }
  const num = (v: string) => (v.trim() === '' ? null : Number(v.replace(/[^\d.]/g, '')) || null)
  const desc = value.description ?? { en: '' }

  return (
    <div className="space-y-3">
      <Field label="Title" htmlFor="title" {...flag('title')}>
        <input id="title" className={inputCls} maxLength={120} value={value.title ?? ''} onChange={(e) => set({ title: e.target.value })} />
        {src('title')}
      </Field>

      <Field label="Sale or rent" {...flag('transaction')}>
        <div className="flex gap-2">
          {(['sale', 'rent'] as Transaction[]).map((tr) => (
            <button
              key={tr}
              type="button"
              aria-pressed={value.transaction === tr}
              onClick={() => set({ transaction: tr })}
              className={`min-h-[52px] flex-1 rounded-xl border font-semibold capitalize ${value.transaction === tr ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white'}`}
            >
              {tr === 'sale' ? 'For sale' : 'For rent'}
            </button>
          ))}
        </div>
      </Field>

      <PriceField value={value.price_inr} onChange={(n) => set({ price_inr: n })} flag={flag('price_inr')} warning={priceSanity(value)} hint={priceHint}>{src('price_inr')}</PriceField>

      <Field label="Property type" htmlFor="ptype" {...flag('property_type')}>
        <select id="ptype" className={inputCls} value={value.property_type ?? ''} onChange={(e) => set({ property_type: (e.target.value || undefined) as PropertyType })}>
          <option value="">Select</option>
          {TYPES.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        {src('property_type')}
      </Field>

      <div className="grid grid-cols-2 gap-2">
        <Field label="City" htmlFor="city" {...flag('city')}>
          <input id="city" className={inputCls} value={value.city ?? ''} onChange={(e) => set({ city: e.target.value })} />
        {src('city')}
        </Field>
        <Field label="Locality" htmlFor="locality" {...flag('locality')}>
          <input id="locality" className={inputCls} value={value.locality ?? ''} onChange={(e) => set({ locality: e.target.value })} />
        {src('locality')}
        </Field>
      </div>

      <Field label="Society / project (optional)" htmlFor="project" {...flag('project_name')}>
        <input id="project" className={inputCls} value={value.project_name ?? ''} onChange={(e) => set({ project_name: e.target.value })} />
        {src('project_name')}
      </Field>

      <div className="grid grid-cols-2 gap-2">
        <Field label="BHK" htmlFor="bhk" {...flag('bhk')}>
          <input id="bhk" className={inputCls} inputMode="decimal" value={value.bhk ?? ''} onChange={(e) => set({ bhk: num(e.target.value) })} />
        {src('bhk')}
        </Field>
        <Field label="Carpet area (sq ft)" htmlFor="carpet" {...flag('carpet_sqft')}>
          <input id="carpet" className={inputCls} inputMode="numeric" value={value.carpet_sqft ?? ''} onChange={(e) => set({ carpet_sqft: num(e.target.value) })} />
        {src('carpet_sqft')}
        </Field>
        <Field label="Floor" htmlFor="floor" {...flag('floor')}>
          <input id="floor" className={inputCls} inputMode="numeric" value={value.floor ?? ''} onChange={(e) => set({ floor: num(e.target.value) })} />
        </Field>
        <Field label="Total floors" htmlFor="tfloors" {...flag('total_floors')}>
          <input id="tfloors" className={inputCls} inputMode="numeric" value={value.total_floors ?? ''} onChange={(e) => set({ total_floors: num(e.target.value) })} />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Field label="Furnishing" htmlFor="furn" {...flag('furnishing')}>
          <select id="furn" className={inputCls} value={value.furnishing ?? ''} onChange={(e) => set({ furnishing: (e.target.value || null) as Furnishing | null })}>
            <option value="">-</option>
            <option value="unfurnished">Unfurnished</option>
            <option value="semi">Semi</option>
            <option value="furnished">Furnished</option>
          </select>
        </Field>
        <Field label="Possession" htmlFor="poss" {...flag('possession')}>
          <select id="poss" className={inputCls} value={value.possession ?? ''} onChange={(e) => set({ possession: e.target.value || null })}>
            <option value="">-</option>
            <option value="ready">Ready</option>
            <option value="under_construction">Under construction</option>
          </select>
        {src('possession')}
        </Field>
      </div>

      <Field label="One unit or whole project?" {...flag('listing_scope')}>
        <div className="flex gap-2">
          {([['single', 'One unit'], ['layout', 'Whole project']] as const).map(([sc, label]) => (
            <button
              key={sc}
              type="button"
              aria-pressed={value.listing_scope === sc}
              onClick={() => set({ listing_scope: sc })}
              className={`min-h-[44px] flex-1 rounded-xl border font-semibold ${value.listing_scope === sc ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white'}`}
            >
              {label}
            </button>
          ))}
        </div>
      </Field>

      <Field label="MahaRERA number (optional)" htmlFor="rera" {...flag('rera_no')}>
        <input id="rera" className={inputCls} placeholder="PR1260002501386" disabled={value.rera_status === 'not_registered'} value={value.rera_no ?? ''}
          onChange={(e) => set({ rera_no: e.target.value.toUpperCase().replace(/\s/g, '') })} />
        {value.rera_no && src('rera_no')}
        {!value.rera_no && value.rera_status !== 'not_registered' && reraCandidates.length > 0 && <ReraPicks candidates={reraCandidates} onPick={set} />}
        <label className="mt-1 flex min-h-[44px] items-center gap-2 text-sm">
          <input type="checkbox" className="h-5 w-5" checked={value.rera_status === 'not_registered'}
            onChange={(e) => set(e.target.checked ? { rera_status: 'not_registered', rera_no: null } : { rera_status: null })} />
          Not registered on MahaRERA
        </label>
      </Field>

      <ChipPicker label="Amenities" options={AMENITIES} value={value.amenities ?? []} onChange={(a) => set({ amenities: a })} />

      {onEditAbout && <AboutSummary about={about} onEdit={onEditAbout} />}

      <Field label="Description" {...flag('description.en')}>
        <div role="tablist" className="mb-2 flex gap-2">
          {(['en', 'hi', 'mr'] as const).map((l) => (
            <button
              key={l}
              type="button"
              role="tab"
              aria-selected={lang === l}
              onClick={() => setLang(l)}
              className={`min-h-[44px] flex-1 rounded-lg text-sm font-semibold ${lang === l ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}
            >
              {l === 'en' ? 'English' : l === 'hi' ? 'हिन्दी' : 'मराठी'}
            </button>
          ))}
        </div>
        <textarea
          aria-label={`Description ${lang}`}
          className={`${inputCls} min-h-[140px] py-3`}
          value={desc[lang] ?? ''}
          onChange={(e) => set({ description: { ...desc, en: desc.en ?? '', [lang]: e.target.value } })}
        />
      </Field>

      <Field label={`${t('addPhotos')} (${photos.length})`} {...flag('media')}>
        {photos.length > 0 ? (
          <div className="flex gap-2 overflow-x-auto">
            {photos.map((m) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img key={m.url} src={m.url} alt="" className="h-20 w-20 flex-none rounded-lg object-cover" />
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">At least 1 photo is needed to publish.</p>
        )}
      </Field>
    </div>
  )
}
