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
