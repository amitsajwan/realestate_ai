'use client'
import React, { useEffect, useState } from 'react'
import { aboutSummaryLines } from '@/lib/app/about'
import { formatInr, groupIndian, parseInr } from '@/lib/app/format'
import { t } from '@/lib/app/strings'
import type { About, Furnishing, ListingInput, PropertyType, Transaction } from '@/lib/app/types'
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
}

function PriceField({ value, onChange, flag, warning }: { value?: number; onChange: (n: number) => void; flag: { error?: string; check?: boolean; required?: boolean }; warning?: string | null }) {
  const [text, setText] = useState(value ? groupIndian(value) : '')
  // Keep the text in sync when the value is replaced from outside (e.g. draft arrives), but not while typing.
  const parsed = parseInr(text)
  useEffect(() => {
    if (value && parseInr(text) !== value) setText(groupIndian(value))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])
  return (
    <Field label="Price (₹)" htmlFor="price" {...flag}>
      <input
        id="price"
        className={inputCls}
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

export function ReviewForm({ value, onChange, confidence = {}, missing = [], errors = {}, about, onEditAbout }: ReviewFormProps) {
  const [lang, setLang] = useState<'en' | 'hi' | 'mr'>('en')
  const set = (patch: ListingInput) => onChange({ ...value, ...patch })
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

      <PriceField value={value.price_inr} onChange={(n) => set({ price_inr: n })} flag={flag('price_inr')} warning={priceSanity(value)} />

      <Field label="Property type" htmlFor="ptype" {...flag('property_type')}>
        <select id="ptype" className={inputCls} value={value.property_type ?? ''} onChange={(e) => set({ property_type: (e.target.value || undefined) as PropertyType })}>
          <option value="">Select</option>
          {TYPES.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </Field>

      <div className="grid grid-cols-2 gap-2">
        <Field label="City" htmlFor="city" {...flag('city')}>
          <input id="city" className={inputCls} value={value.city ?? ''} onChange={(e) => set({ city: e.target.value })} />
        </Field>
        <Field label="Locality" htmlFor="locality" {...flag('locality')}>
          <input id="locality" className={inputCls} value={value.locality ?? ''} onChange={(e) => set({ locality: e.target.value })} />
        </Field>
      </div>

      <Field label="Society / project (optional)" htmlFor="project" {...flag('project_name')}>
        <input id="project" className={inputCls} value={value.project_name ?? ''} onChange={(e) => set({ project_name: e.target.value })} />
      </Field>

      <div className="grid grid-cols-2 gap-2">
        <Field label="BHK" htmlFor="bhk" {...flag('bhk')}>
          <input id="bhk" className={inputCls} inputMode="decimal" value={value.bhk ?? ''} onChange={(e) => set({ bhk: num(e.target.value) })} />
        </Field>
        <Field label="Carpet area (sq ft)" htmlFor="carpet" {...flag('carpet_sqft')}>
          <input id="carpet" className={inputCls} inputMode="numeric" value={value.carpet_sqft ?? ''} onChange={(e) => set({ carpet_sqft: num(e.target.value) })} />
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
        </Field>
      </div>

      <Field label="RERA number (optional)" htmlFor="rera" {...flag('rera_no')}>
        <input id="rera" className={inputCls} value={value.rera_no ?? ''} onChange={(e) => set({ rera_no: e.target.value })} />
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

      <Field label={`${t('addPhotos')} (${(value.media ?? []).length})`} {...flag('media')}>
        {(value.media ?? []).length > 0 ? (
          <div className="flex gap-2 overflow-x-auto">
            {(value.media ?? []).map((m) => (
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
