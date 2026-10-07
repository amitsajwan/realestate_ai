'use client'
import { compressImage } from '@/lib/app/imageCompress'
import { EMPTY_EXTRAS, ProfileExtras, type ProfileExtrasValue } from './ProfileExtras'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import React, { useEffect, useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import { displayPhone, normalizePhone } from '@/lib/app/format'
import { getToken, saveSession, saveSiteUrl } from '@/lib/app/session'
import { t } from '@/lib/app/strings'
import { PRESETS, PRESET_IDS } from '@/lib/site/presets'
import type { SiteResult } from '@/lib/app/types'
import { FixtureBanner } from './AppShell'
import { ShareBar } from './ShareBar'
import { Btn, ErrorBox, Field, LinkBtn, inputCls } from './ui'

const LANGS = ['English', 'Hindi', 'Marathi', 'Gujarati', 'Tamil', 'Telugu', 'Kannada', 'Bengali']
const SPECIALTIES = ['Resale flats', 'New projects', 'Rentals', 'Plots', 'Commercial', 'Luxury homes']
const RESEND_SECONDS = 30

type Step = 'phone' | 'otp' | 'profile' | 'done'

function toggle(list: string[], v: string) {
  return list.includes(v) ? list.filter((x) => x !== v) : [...list, v]
}

export function JoinFlow() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('phone')
  const [phoneRaw, setPhoneRaw] = useState('')
  useEffect(() => { // /join?phone=9876543210 (the link in the free-trial WhatsApp reply) fills the number in
    const p = new URLSearchParams(window.location.search).get('phone')
    if (p && /^[6-9]\d{9}$/.test(p)) setPhoneRaw(p)
  }, [])
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [devCode, setDevCode] = useState<string | null>(null)
  const [invite, setInvite] = useState(false)
  const [left, setLeft] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [city, setCity] = useState('')
  const [languages, setLanguages] = useState<string[]>(['English', 'Hindi'])
  const [specialties, setSpecialties] = useState<string[]>([])
  const [extras, setExtras] = useState<ProfileExtrasValue>(EMPTY_EXTRAS)
  const [site, setSite] = useState<SiteResult | null>(null)
  const [businessName, setBusinessName] = useState('')
  const [preset, setPreset] = useState('navy-gold')

  useEffect(() => {
    if (getToken()) router.replace('/studio') // already signed in
  }, [router])

  useEffect(() => {
    if (left <= 0) return
    const id = setTimeout(() => setLeft((s) => s - 1), 1000)
    return () => clearTimeout(id)
  }, [left])

  async function sendOtp(e?: React.FormEvent) {
    e?.preventDefault()
    const normalized = normalizePhone(phoneRaw)
    if (!normalized) return setError(t('phoneInvalid'))
    setBusy(true)
    setError(null)
    try {
      const r = await api.requestOtp(normalized)
      setPhone(normalized)
      setDevCode(r.dev_code ?? null)
      setInvite(r.mode === 'invite')
      setCode('')
      setLeft(r.mode === 'invite' ? 0 : RESEND_SECONDS)
      setStep('otp')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function verify(c: string) {
    if (c.length < 6 || busy) return
    setBusy(true)
    setError(null)
    try {
      const r = await api.verifyOtp(phone, c)
      saveSession({ token: r.access_token, siteUrl: r.site_url ?? null, phone })
      if (r.has_site) router.replace('/studio')
      else setStep('profile')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false) // the next step (site form) must not inherit the busy state
    }
  }

  async function makeSite(e: React.FormEvent) {
    e.preventDefault()
    if (name.trim().length < 2 || city.trim().length < 2) return setError('Please fill your name and city')
    setBusy(true)
    setError(null)
    try {
      // optional extras: upload the photo / logo first, then create the site with their URLs
      const [photo, logo] = await Promise.all([extras.photo, extras.logo].map(async (f) => (f ? (await api.uploadImages([await compressImage(f)]))[0]?.url : undefined)))
      const r = await api.createSite({
        name: name.trim(), city: city.trim(), languages, specialties,
        ...(businessName.trim() ? { business_name: businessName.trim() } : {}), preset,
        ...(photo ? { photo } : {}), ...(logo ? { logo } : {}),
        ...(extras.instagram.trim() ? { instagram: extras.instagram.trim() } : {}),
        ...(extras.facebook.trim() ? { facebook_url: extras.facebook.trim() } : {}),
      })
      saveSiteUrl(r.site_url)
      setSite(r)
      setStep('done')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const isDev = process.env.NODE_ENV !== 'production'

  return (
    <div data-surface="v2" className="fixed inset-0 z-50 overflow-y-auto bg-gray-50 text-gray-900">
      <FixtureBanner />
      <div className="mx-auto max-w-md space-y-5 px-4 py-8">
        {step === 'phone' && (
          <form onSubmit={sendOtp} className="space-y-5">
            <h1 className="text-3xl font-bold">Get your property website in 1 minute</h1>
            <p className="text-gray-700">Sign in with your mobile number. Your website, share-ready posts and buyer lead cards are all in one place.</p>
            <Field label={t('phoneLabel')} htmlFor="phone">
              <div className="flex gap-2">
                <span className="flex min-h-[52px] items-center rounded-xl border border-gray-300 bg-gray-100 px-3 font-semibold">+91</span>
                <input
                  id="phone"
                  className={inputCls}
                  type="tel"
                  inputMode="numeric"
                  autoComplete="tel-national"
                  placeholder={t('phonePlaceholder')}
                  value={phoneRaw}
                  onChange={(e) => setPhoneRaw(e.target.value)}
                  autoFocus
                />
              </div>
            </Field>
            {error && <ErrorBox message={error} />}
            <Btn type="submit" disabled={busy}>{busy ? t('loading') : t('sendOtp')}</Btn>
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-gray-800">
              <p className="font-semibold">Free trial for agents in Pune: your first 3 properties free. No code yet? Send TRIAL to Avasetu on WhatsApp.</p>
              <p className="mt-1">Your phone number is never shown publicly. No app to install.</p>
              <Link href="/trial" className="mt-2 flex min-h-[44px] items-center font-semibold text-blue-800 underline">No code yet? Claim your free trial</Link>
            </div>
          </form>
        )}

        {step === 'otp' && (
          <div className="space-y-5">
            <h1 className="text-2xl font-bold">{invite ? t('inviteLabel') : t('otpLabel')}</h1>
            <p className="text-gray-600">
              {invite ? t('inviteFor') : t('otpSentTo')} {displayPhone(phone)}{' '}
              <button type="button" className="min-h-[44px] font-semibold text-blue-700 underline" onClick={() => { setStep('phone'); setError(null) }}>
                {t('changeNumber')}
              </button>
            </p>
            <input
              aria-label={t('otpLabel')}
              className={`${inputCls} text-center text-3xl tracking-[0.5em]`}
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={code}
              autoFocus
              onChange={(e) => {
                const v = e.target.value.replace(/\D/g, '').slice(0, 6)
                setCode(v)
                if (v.length === 6) verify(v)
              }}
            />
            {isDev && devCode && (
              <div className="flex items-center justify-between rounded-xl border border-dashed border-amber-400 bg-amber-50 p-3 text-sm">
                <span>{t('devHint')} <b>{devCode}</b></span>
                <Btn variant="secondary" block={false} className="!min-h-[44px]" onClick={() => { setCode(devCode); verify(devCode) }}>
                  {t('autofill')}
                </Btn>
              </div>
            )}
            {error && <ErrorBox message={error} />}
            <Btn disabled={busy || code.length < 6} onClick={() => verify(code)}>{busy ? t('loading') : t('verify')}</Btn>
            {invite ? (
              <p className="text-sm text-gray-600">{t('inviteHelp')}</p>
            ) : (
              <Btn variant="ghost" disabled={left > 0 || busy} onClick={() => sendOtp()}>
                {left > 0 ? `${t('resendIn')} ${left}s` : t('resend')}
              </Btn>
            )}
          </div>
        )}

        {step === 'profile' && (
          <form onSubmit={makeSite} className="space-y-5">
            <h1 className="text-2xl font-bold">Tell us about you</h1>
            <Field label={t('yourName')} htmlFor="name">
              <input id="name" className={inputCls} value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" autoFocus />
            </Field>
            <Field label={t('yourCity')} htmlFor="city">
              <input id="city" className={inputCls} value={city} onChange={(e) => setCity(e.target.value)} placeholder="Pune" />
            </Field>
            <Field label="Business name (optional)" htmlFor="biz">
              <input id="biz" className={inputCls} value={businessName} onChange={(e) => setBusinessName(e.target.value)} placeholder="e.g. Kulkarni Homes" maxLength={60} />
            </Field>
            <fieldset>
              <legend className="mb-2 text-sm font-medium text-gray-700">Colour theme for your website</legend>
              <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Colour theme">
                {PRESET_IDS.map((id) => (
                  <button key={id} type="button" role="radio" aria-checked={preset === id} aria-label={PRESETS[id].label} data-testid={'join-preset-' + id} onClick={() => setPreset(id)}
                    className={`flex min-h-[44px] items-center gap-2 rounded-full border-2 px-3 text-sm font-semibold ${preset === id ? 'border-blue-600 bg-blue-50' : 'border-gray-200 bg-white'}`}>
                    <span aria-hidden className="h-5 w-5 rounded-full border border-black/10" style={{ background: `linear-gradient(135deg, ${PRESETS[id].primary} 60%, ${PRESETS[id].accent} 60%)` }} />
                    {PRESETS[id].label}
                  </button>
                ))}
              </div>
              <p className="mt-1 text-xs text-gray-500">You can add a logo, banner and RERA number later under My brand.</p>
            </fieldset>
            <ChipPicker label={t('languages')} options={LANGS} value={languages} onChange={setLanguages} />
            <ChipPicker label={t('specialties')} options={SPECIALTIES} value={specialties} onChange={setSpecialties} />
            <ProfileExtras value={extras} onChange={setExtras} />
            {error && <ErrorBox message={error} />}
            <Btn type="submit" disabled={busy}>{busy ? t('loading') : t('createSite')}</Btn>
          </form>
        )}

        {step === 'done' && site && (
          <div className="space-y-5 text-center">
            <div className="text-5xl" aria-hidden>🎉</div>
            <h1 className="text-2xl font-bold">{t('siteLive')}</h1>
            <p className="text-gray-600">{site.tagline}</p>
            <a href={site.site_url} target="_blank" rel="noopener noreferrer" className="block break-all rounded-xl bg-white p-3 font-semibold text-blue-700 underline">
              {site.site_url}
            </a>
            <ShareBar url={site.site_url} message={`Namaste! Visit my property website:`} />
            <LinkBtn href="/studio/listings/new">{t('addFirstListing')}</LinkBtn>
            <Link href="/studio" className="block min-h-[44px] py-3 font-semibold text-gray-600">{t('goToStudio')}</Link>
          </div>
        )}
      </div>
    </div>
  )
}

export function ChipPicker({ label, options, value, onChange }: { label: string; options: string[]; value: string[]; onChange: (v: string[]) => void }) {
  return (
    <fieldset>
      <legend className="mb-2 text-sm font-medium text-gray-700">{label}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((o) => {
          const on = value.includes(o)
          return (
            <button
              key={o}
              type="button"
              aria-pressed={on}
              onClick={() => onChange(toggle(value, o))}
              className={`min-h-[44px] rounded-full border px-4 text-sm font-semibold ${on ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white text-gray-700'}`}
            >
              {o}
            </button>
          )
        })}
      </div>
    </fieldset>
  )
}
