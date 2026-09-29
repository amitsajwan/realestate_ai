'use client'
import React from 'react'
import { t } from '@/lib/app/strings'
import type { ListingStatus, Stage, Temperature } from '@/lib/app/types'

type BtnProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'whatsapp' | 'danger' | 'ghost'
  block?: boolean
}

const VARIANTS: Record<NonNullable<BtnProps['variant']>, string> = {
  primary: 'bg-blue-600 text-white active:bg-blue-700 disabled:bg-blue-300',
  secondary: 'bg-white text-blue-700 border border-blue-200 active:bg-blue-50 disabled:text-gray-400',
  whatsapp: 'bg-green-600 text-white active:bg-green-700 disabled:bg-green-300',
  danger: 'bg-white text-red-600 border border-red-200 active:bg-red-50',
  ghost: 'bg-transparent text-gray-700 active:bg-gray-100',
}

/** Big touch target (>= 48px). */
export function Btn({ variant = 'primary', block = true, className = '', ...rest }: BtnProps) {
  return (
    <button
      type="button"
      {...rest}
      className={`min-h-[52px] rounded-xl px-5 text-base font-semibold transition-colors ${block ? 'w-full' : ''} ${VARIANTS[variant]} ${className}`}
    />
  )
}

/** Anchor that looks like a Btn. */
export function LinkBtn({
  variant = 'primary',
  block = true,
  className = '',
  ...rest
}: React.AnchorHTMLAttributes<HTMLAnchorElement> & Pick<BtnProps, 'variant' | 'block'>) {
  return (
    <a
      {...rest}
      className={`flex min-h-[52px] items-center justify-center rounded-xl px-5 text-base font-semibold ${block ? 'w-full' : ''} ${VARIANTS[variant]} ${className}`}
    />
  )
}

export function Chip({ children, tone = 'gray', className = '' }: { children: React.ReactNode; tone?: string; className?: string }) {
  const tones: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-700',
    green: 'bg-green-100 text-green-800',
    amber: 'bg-amber-100 text-amber-800',
    red: 'bg-red-100 text-red-700',
    blue: 'bg-blue-100 text-blue-800',
    purple: 'bg-purple-100 text-purple-800',
  }
  return <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${tones[tone] ?? tones.gray} ${className}`}>{children}</span>
}

const STATUS_TONE: Record<ListingStatus, string> = {
  draft: 'gray', live: 'green', under_offer: 'amber', sold: 'purple', rented: 'purple', paused: 'gray', expired: 'red',
}
export function StatusChip({ status }: { status: ListingStatus }) {
  return <Chip tone={STATUS_TONE[status]}>{status.replace('_', ' ')}</Chip>
}

const TEMP_TONE: Record<Temperature, string> = { hot: 'red', warm: 'amber', cold: 'blue' }
export function TempChip({ temperature, score }: { temperature: Temperature; score?: number }) {
  return (
    <Chip tone={TEMP_TONE[temperature]}>
      {t(temperature)}
      {score !== undefined ? ` ${score}` : ''}
    </Chip>
  )
}

export const STAGES: Array<{ key: Stage; label: string }> = [
  { key: 'new', label: 'New' },
  { key: 'contacted', label: 'Contacted' },
  { key: 'site_visit', label: 'Site visit' },
  { key: 'negotiating', label: 'Negotiating' },
  { key: 'won', label: 'Won' },
  { key: 'lost', label: 'Lost' },
]

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
      <p>{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="mt-2 min-h-[44px] font-semibold underline">
          {t('tryAgain')}
        </button>
      )}
    </div>
  )
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-10 text-gray-500" role="status">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
      <span className="text-sm">{label ?? t('loading')}</span>
    </div>
  )
}

export const inputCls =
  'w-full min-h-[52px] rounded-xl border border-gray-300 bg-white px-4 text-base text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200'

export function Field({
  label,
  error,
  check,
  required,
  children,
  htmlFor,
}: {
  label: string
  error?: string
  check?: boolean
  required?: boolean
  children: React.ReactNode
  htmlFor?: string
}) {
  const flagged = !!error || check
  return (
    <div className={`rounded-xl p-2 ${error ? 'bg-red-50' : check ? 'bg-amber-50' : ''}`} data-flag={error ? 'error' : check ? 'check' : undefined}>
      <label htmlFor={htmlFor} className="mb-1 flex items-center justify-between text-sm font-medium text-gray-700">
        <span>{label}</span>
        {flagged && (
          <span className={`text-xs font-semibold ${error ? 'text-red-600' : 'text-amber-700'}`}>
            {error ? (required ? t('required') : error) : t('pleaseCheck')}
          </span>
        )}
      </label>
      {children}
      {error && !required && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}

export function PageTitle({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h1 className="text-2xl font-bold text-gray-900">{children}</h1>
      {action}
    </div>
  )
}
