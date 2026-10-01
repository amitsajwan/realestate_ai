'use client'
import React, { useEffect, useRef, useState } from 'react'
import { assetUrl, type BrandingDoc, type BrandingPatch } from '@/lib/app/branding'
import { errorMessage } from '@/lib/app/client'
import { PRESETS, PRESET_IDS, BANNER_OVERLAY, type PresetId } from '@/lib/site/presets'
import { monogram, resolveTheme, safeCustomPrimary, themeVars } from '@/lib/site/theme'
import type { AgentBranding } from '@/lib/site/types'
import { Btn, ErrorBox, Field, Spinner, inputCls } from './ui'

export interface BrandEditorProps {
  /** Set by the owner screen when editing another agent; passed back to the injected callbacks. */
  agentId?: string
  loadBranding: (agentId?: string) => Promise<BrandingDoc>
  saveBranding: (patch: BrandingPatch, agentId?: string) => Promise<BrandingDoc>
  uploadImage: (file: File, agentId?: string) => Promise<string>
  onSaved?: (doc: BrandingDoc) => void
}

const AREA_SUGGESTIONS = ['Baner', 'Aundh', 'Kothrud', 'Wakad', 'Hinjewadi', 'Kharadi', 'Wagholi', 'Hadapsar', 'Viman Nagar', 'Koregaon Park', 'Pashan', 'Balewadi', 'Magarpatta', 'Bavdhan']
const LANGUAGES = ['English', 'Hindi', 'Marathi', 'Gujarati', 'Tamil', 'Telugu', 'Kannada', 'Bengali']
const MAX_AREAS = 6

interface Draft {
  business_name: string
  tagline: string
  about: string
  preset: PresetId
  custom_on: boolean
  custom_primary: string
  rera_agent_no: string
  areas: string[]
  languages: string[]
  years_experience: string
  logo: string
  banner: string
}

function toDraft(b: AgentBranding): Draft {
  return {
    business_name: b.business_name || '', tagline: b.tagline || '', about: b.about || '',
    preset: (b.preset && b.preset in PRESETS ? b.preset : 'navy-gold') as PresetId,
    custom_on: !!b.custom_primary, custom_primary: b.custom_primary || '#1f3a8a',
    rera_agent_no: b.rera_agent_no || '', areas: b.areas || [], languages: b.languages || [],
    years_experience: b.years_experience != null ? String(b.years_experience) : '',
    logo: b.logo || '', banner: b.banner || '',
  }
}

function toggle(list: string[], v: string, max = 99) {
  if (list.includes(v)) return list.filter((x) => x !== v)
  return list.length >= max ? list : [...list, v]
}

/** Live miniature of the public page header + hero for the draft (same theme code as the real site). */
export function BrandPreview({ draft, agentName, logoSrc, bannerSrc }: { draft: Draft; agentName: string; logoSrc?: string; bannerSrc?: string }) {
  const branding: AgentBranding = { preset: draft.preset, custom_primary: draft.custom_on ? draft.custom_primary : null }
  const t = resolveTheme(branding)
  const name = draft.business_name.trim() || agentName || 'Your business'
  const light = !bannerSrc && t.id === 'cream-ink'
  return (
    <div data-testid="brand-preview" data-preset={t.id} style={themeVars(branding) as React.CSSProperties} className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 px-3 py-2" style={{ background: 'var(--site-header-bg)', color: 'var(--site-header-fg)' }}>
        {logoSrc ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={logoSrc} alt="" className="h-7 w-auto max-w-[5rem] rounded bg-white object-contain p-0.5" />
        ) : (
          <span aria-hidden className="flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-extrabold" style={{ background: 'var(--site-accent)', color: 'var(--site-on-accent)' }}>{monogram(name)}</span>
        )}
        <span className="truncate text-sm font-bold">{name}</span>
        <span className="ml-auto text-[10px] opacity-80">About  Contact</span>
      </div>
      <div className="relative px-4 pb-4 pt-5" style={bannerSrc ? { background: BANNER_OVERLAY.solid, color: '#fff' } : { backgroundImage: 'linear-gradient(165deg, var(--site-hero-from), var(--site-hero-to))', color: 'var(--site-hero-fg)' }}>
        {bannerSrc && (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={bannerSrc} alt="" className="absolute inset-0 h-full w-full object-cover" />
            <div aria-hidden className="absolute inset-0" style={{ backgroundImage: `linear-gradient(180deg, ${BANNER_OVERLAY.from}, ${BANNER_OVERLAY.to})` }} />
          </>
        )}
        <div className="relative">
          <span className="inline-block rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide" style={{ background: 'var(--site-accent)', color: 'var(--site-on-accent)' }}>
            Pune property{draft.areas[0] ? ' · ' + draft.areas[0] : ''}
          </span>
          <p className="mt-2 text-lg font-extrabold leading-tight">{draft.tagline.trim() || 'Homes in Pune, shared clearly'}</p>
          <span className="mt-3 inline-block px-4 py-1.5 text-xs font-bold" style={{ background: light ? 'var(--site-primary)' : 'var(--site-accent)', color: light ? '#fff' : 'var(--site-on-accent)', borderRadius: 'var(--site-radius)' }}>I&apos;m interested</span>
        </div>
      </div>
    </div>
  )
}

function ImagePick({ id, label, hint, src, busy, onPick, onClear, wide }: { id: string; label: string; hint: string; src: string; busy: boolean; onPick: (f: File) => void; onClear: () => void; wide?: boolean }) {
  const ref = useRef<HTMLInputElement>(null)
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-gray-700">{label}</p>
      <div className={'flex items-center justify-center overflow-hidden rounded-xl border border-dashed border-gray-300 bg-gray-100 text-sm text-gray-500 ' + (wide ? 'aspect-[8/3] w-full' : 'h-20 w-40')}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {src ? <img src={src} alt={label + ' preview'} className={'h-full w-full ' + (wide ? 'object-cover' : 'object-contain p-1')} /> : <span>{wide ? 'No banner yet' : 'No logo yet'}</span>}
      </div>
      <p className="text-xs text-gray-500">{hint}</p>
      <div className="flex gap-2">
        <Btn variant="secondary" block={false} disabled={busy} onClick={() => ref.current?.click()}>{busy ? 'Uploading...' : src ? 'Change' : 'Add'}</Btn>
        {src && <Btn variant="ghost" block={false} disabled={busy} onClick={onClear}>Remove</Btn>}
      </div>
      <input ref={ref} id={id} data-testid={id} type="file" accept="image/*" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) onPick(f); e.target.value = '' }} />
    </div>
  )
}

function Chips({ label, options, value, onChange, max }: { label: string; options: string[]; value: string[]; onChange: (v: string[]) => void; max?: number }) {
  const all = [...options, ...value.filter((v) => !options.includes(v))]
  return (
    <fieldset>
      <legend className="mb-2 text-sm font-medium text-gray-700">{label}</legend>
      <div className="flex flex-wrap gap-2">
        {all.map((o) => {
          const on = value.includes(o)
          return (
            <button key={o} type="button" aria-pressed={on} onClick={() => onChange(toggle(value, o, max))}
              className={`min-h-[44px] rounded-full border px-4 text-sm font-semibold ${on ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white text-gray-700'}`}>{o}</button>
          )
        })}
      </div>
    </fieldset>
  )
}

/** Edit the agent's public brand: logo, banner, preset, colour, texts, areas, languages and RERA agent number. Reusable: all I/O is injected. */
export function BrandEditor({ agentId, loadBranding, saveBranding, uploadImage, onSaved }: BrandEditorProps) {
  const [doc, setDoc] = useState<BrandingDoc | null>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<'logo' | 'banner' | 'save' | null>(null)
  const [saved, setSaved] = useState(false)
  const [custom, setCustom] = useState('')

  useEffect(() => {
    let alive = true
    loadBranding(agentId).then((d) => { if (alive) { setDoc(d); setDraft(toDraft(d.branding_data || {})) } }).catch((e) => { if (alive) setError(errorMessage(e)) })
    return () => { alive = false }
  }, [agentId, loadBranding])

  if (error && !draft) return <ErrorBox message={error} />
  if (!draft || !doc) return <Spinner />
  const set = (patch: Partial<Draft>) => { setSaved(false); setDraft({ ...draft, ...patch }) }
  const customOk = !draft.custom_on || safeCustomPrimary(draft.custom_primary) !== null

  async function pick(kind: 'logo' | 'banner', file: File) {
    setBusy(kind)
    setError(null)
    try {
      const url = await uploadImage(file, agentId)
      set({ [kind]: url } as Partial<Draft>)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  async function save() {
    if (!draft || !customOk) return
    setBusy('save')
    setError(null)
    const years = draft.years_experience.trim()
    const patch: BrandingPatch = {
      business_name: draft.business_name.trim(), tagline: draft.tagline.trim(), about: draft.about.trim(),
      preset: draft.preset, custom_primary: draft.custom_on ? draft.custom_primary : '',
      rera_agent_no: draft.rera_agent_no.trim(), areas: draft.areas, languages: draft.languages,
      years_experience: years ? Number(years) : null, logo: draft.logo, banner: draft.banner,
    }
    try {
      const d = await saveBranding(patch, agentId)
      setDoc(d)
      setDraft(toDraft(d.branding_data || {}))
      setSaved(true)
      onSaved?.(d)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  const addCustomArea = () => {
    const v = custom.trim()
    if (v && !draft.areas.includes(v)) set({ areas: toggle(draft.areas, v, MAX_AREAS) })
    setCustom('')
  }

  return (
    <div data-testid="brand-editor" className="space-y-5">
      <div>
        <BrandPreview draft={draft} agentName={doc.agent_name} logoSrc={assetUrl(draft.logo)} bannerSrc={assetUrl(draft.banner)} />
      </div>

      <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
        <h2 className="text-base font-semibold">Look and feel</h2>
        <div role="radiogroup" aria-label="Colour theme" className="grid grid-cols-2 gap-2">
          {PRESET_IDS.map((id) => {
            const p = PRESETS[id]
            const on = draft.preset === id
            return (
              <button key={id} type="button" role="radio" aria-checked={on} data-testid={'preset-' + id} onClick={() => set({ preset: id })}
                className={`flex min-h-[56px] items-center gap-2 rounded-xl border-2 p-2 text-left ${on ? 'border-blue-600 bg-blue-50' : 'border-gray-200 bg-white'}`}>
                <span aria-hidden className="flex h-8 w-12 shrink-0 overflow-hidden rounded-md border border-black/10">
                  <span className="w-1/2" style={{ background: p.primary }} /><span className="w-1/4" style={{ background: p.heroTo }} /><span className="w-1/4" style={{ background: p.accent }} />
                </span>
                <span className="min-w-0 leading-tight"><span className="block text-sm font-semibold">{p.label}</span><span className="block text-xs text-gray-500">{p.blurb}</span></span>
              </button>
            )
          })}
        </div>
        <label className="flex min-h-[44px] items-center gap-2 text-sm">
          <input type="checkbox" checked={draft.custom_on} onChange={(e) => set({ custom_on: e.target.checked })} className="h-5 w-5" />
          Use my own main colour (optional)
        </label>
        {draft.custom_on && (
          <div className="flex items-center gap-3">
            <input type="color" aria-label="Pick colour" value={/^#[0-9a-f]{6}$/i.test(draft.custom_primary) ? draft.custom_primary : '#1f3a8a'} onChange={(e) => set({ custom_primary: e.target.value })} className="h-12 w-14 rounded-lg border border-gray-300" />
            <input aria-label="Colour code" className={inputCls} value={draft.custom_primary} onChange={(e) => set({ custom_primary: e.target.value })} maxLength={7} autoCapitalize="none" />
          </div>
        )}
        {!customOk && <p role="alert" className="text-sm text-red-600">That colour is too light for white text. Choose a darker shade.</p>}
      </section>

      <section className="space-y-4 rounded-2xl border border-gray-200 bg-white p-4">
        <h2 className="text-base font-semibold">Logo and banner</h2>
        <ImagePick id="brand-logo" label="Logo" hint="Square or wide, a plain background works best. It is shown small in your header." src={assetUrl(draft.logo)} busy={busy === 'logo'} onPick={(f) => pick('logo', f)} onClear={() => set({ logo: '' })} />
        <ImagePick id="brand-banner" label="Banner photo" hint="A wide landscape photo, about 1600 x 600 px. The middle stays visible on phones, so keep faces and text away from the edges. We darken it so your words stay readable." src={assetUrl(draft.banner)} busy={busy === 'banner'} onPick={(f) => pick('banner', f)} onClear={() => set({ banner: '' })} wide />
      </section>

      <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
        <h2 className="text-base font-semibold">About your business</h2>
        <Field label="Business name" htmlFor="brand-name"><input id="brand-name" className={inputCls} value={draft.business_name} maxLength={60} onChange={(e) => set({ business_name: e.target.value })} placeholder="Kulkarni Homes" /></Field>
        <Field label="Tagline" htmlFor="brand-tagline"><input id="brand-tagline" className={inputCls} value={draft.tagline} maxLength={90} onChange={(e) => set({ tagline: e.target.value })} placeholder="Aundh and Baner homes, explained properly" /></Field>
        <Field label="About you" htmlFor="brand-about"><textarea id="brand-about" className={inputCls + ' min-h-[110px] py-3'} value={draft.about} maxLength={600} onChange={(e) => set({ about: e.target.value })} placeholder="A few lines for buyers. No phone numbers or links." /></Field>
        <p className="text-xs text-gray-500">Phone numbers and web links are not allowed in these fields. Buyers reach you through your site.</p>
        <Chips label={`Areas you cover (up to ${MAX_AREAS}, Pune only)`} options={AREA_SUGGESTIONS} value={draft.areas} onChange={(v) => set({ areas: v })} max={MAX_AREAS} />
        <div className="flex gap-2">
          <input aria-label="Add another area" className={inputCls} value={custom} onChange={(e) => setCustom(e.target.value)} placeholder="Another locality in Pune" onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addCustomArea() } }} />
          <Btn variant="secondary" block={false} onClick={addCustomArea}>Add</Btn>
        </div>
        <Chips label="Languages you speak" options={LANGUAGES} value={draft.languages} onChange={(v) => set({ languages: v })} max={6} />
        <Field label="Years in property (optional)" htmlFor="brand-years"><input id="brand-years" inputMode="numeric" className={inputCls} value={draft.years_experience} onChange={(e) => set({ years_experience: e.target.value.replace(/\D/g, '').slice(0, 2) })} placeholder="9" /></Field>
        <Field label="MahaRERA agent registration number (optional)" htmlFor="brand-rera">
          <input id="brand-rera" className={inputCls} value={draft.rera_agent_no} maxLength={20} autoCapitalize="characters" onChange={(e) => set({ rera_agent_no: e.target.value.toUpperCase() })} placeholder="A52100012345" />
        </Field>
        <p className="text-xs text-gray-500">Shown on your page as stated by you. PUNE Property does not verify it and does not call you &quot;verified&quot;.</p>
      </section>

      {error && <ErrorBox message={error} />}
      {saved && <p role="status" className="rounded-xl bg-green-50 p-3 text-sm font-medium text-green-800">Saved. Your site now shows this look.</p>}
      <Btn onClick={save} disabled={busy !== null || !customOk}>{busy === 'save' ? 'Saving...' : 'Save my brand'}</Btn>
    </div>
  )
}
