'use client'
import React, { useEffect, useMemo, useRef } from 'react'
import { Btn, Field, inputCls } from './ui'

export interface ProfileExtrasValue {
  instagram: string
  facebook: string
  photo: File | null
  logo: File | null
}
export const EMPTY_EXTRAS: ProfileExtrasValue = { instagram: '', facebook: '', photo: null, logo: null }

function Pick({ label, hint, file, onChange, round }: { label: string; hint: string; file: File | null; onChange: (f: File | null) => void; round?: boolean }) {
  const ref = useRef<HTMLInputElement>(null)
  const url = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])
  useEffect(() => () => { if (url) URL.revokeObjectURL(url) }, [url])
  return (
    <div className="flex items-center gap-3">
      <div className={'flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden bg-gray-100 text-2xl ' + (round ? 'rounded-full' : 'rounded-xl')}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {url ? <img src={url} alt="" className="h-full w-full object-cover" /> : <span aria-hidden>{round ? '🙂' : '🏷️'}</span>}
      </div>
      <div className="flex-1">
        <p className="font-medium">{label}</p>
        <p className="text-sm text-gray-500">{hint}</p>
      </div>
      <Btn variant="secondary" onClick={() => ref.current?.click()}>{file ? 'Change' : 'Add'}</Btn>
      <input ref={ref} type="file" accept="image/*" hidden data-testid={'extras-' + label.toLowerCase().replace(/\W+/g, '-')}
        onChange={(e) => { onChange(e.target.files?.[0] ?? null); e.target.value = '' }} />
    </div>
  )
}

/** Optional extras when an agent joins: profile photo, logo, Instagram and Facebook. Everything can be skipped. */
export function ProfileExtras({ value, onChange }: { value: ProfileExtrasValue; onChange: (v: ProfileExtrasValue) => void }) {
  const set = (patch: Partial<ProfileExtrasValue>) => onChange({ ...value, ...patch })
  return (
    <fieldset className="space-y-4 rounded-2xl border border-gray-200 bg-white p-4">
      <legend className="px-1 text-sm font-semibold text-gray-700">Optional: make it yours</legend>
      <Pick label="Your photo" hint="Shown on your site" file={value.photo} onChange={(f) => set({ photo: f })} round />
      <Pick label="Your logo" hint="If you have one" file={value.logo} onChange={(f) => set({ logo: f })} />
      <Field label="Instagram" htmlFor="ig">
        <input id="ig" className={inputCls} value={value.instagram} onChange={(e) => set({ instagram: e.target.value })} placeholder="@yourhandle" autoCapitalize="none" autoCorrect="off" />
      </Field>
      <Field label="Facebook page" htmlFor="fb">
        <input id="fb" className={inputCls} value={value.facebook} onChange={(e) => set({ facebook: e.target.value })} placeholder="facebook.com/yourpage" autoCapitalize="none" autoCorrect="off" />
      </Field>
      <p className="text-sm text-gray-500">We only show these as links on your site. We never ask for your passwords.</p>
    </fieldset>
  )
}
