'use client'
/**
 * Placeholder for stream A1's BrandEditor (components/app/BrandEditor.tsx), same props. It covers only what the backend
 * can store today: logo and photo. When A1 is merged, change the import in BrandEditorSlot.tsx and delete this file.
 */
import React, { useEffect, useState } from 'react'
import { ErrorBox } from '../ui'

export interface BrandEditorProps {
  agentId?: string
  loadBranding: () => Promise<Record<string, unknown>>
  saveBranding: (data: Record<string, unknown>) => Promise<unknown>
  uploadImage: (file: File) => Promise<string>
}

function ImageRow({ label, field, value, busy, onPick }: { label: string; field: string; value: string; busy: boolean; onPick: (f: File) => void }) {
  return (
    <div className="flex items-center gap-3">
      {value ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={value} alt={label} className="h-14 w-14 rounded-xl border border-gray-200 object-cover" />
      ) : (
        <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-dashed border-gray-300 text-xs text-gray-400">none</div>
      )}
      <label className="flex min-h-[48px] flex-1 cursor-pointer items-center justify-center rounded-xl border border-blue-200 bg-white px-3 text-sm font-semibold text-blue-700">
        {busy ? 'Uploading...' : value ? `Change ${label.toLowerCase()}` : `Add ${label.toLowerCase()}`}
        <input type="file" accept="image/*" className="sr-only" data-testid={`pick-${field}`} onChange={(e) => e.target.files?.[0] && onPick(e.target.files[0])} />
      </label>
    </div>
  )
}

export function BrandEditor({ loadBranding, saveBranding, uploadImage }: BrandEditorProps) {
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    loadBranding().then(setData).catch(() => setData({}))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function pick(field: 'logo' | 'photo', file: File) {
    setBusy(field)
    setError(null)
    try {
      const url = await uploadImage(file)
      await saveBranding({ [field]: url })
      setData((d) => ({ ...(d ?? {}), [field]: url }))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save')
    } finally {
      setBusy(null)
    }
  }
  if (!data) return <p className="text-sm text-gray-500">Loading...</p>
  return (
    <div className="space-y-3">
      <ImageRow label="Logo" field="logo" value={String(data.logo ?? '')} busy={busy === 'logo'} onPick={(f) => pick('logo', f)} />
      <ImageRow label="Photo" field="photo" value={String(data.photo ?? '')} busy={busy === 'photo'} onPick={(f) => pick('photo', f)} />
      <p className="text-xs text-gray-500">Banner, colours, business name, tagline, about and RERA number arrive with the full brand editor.</p>
      {error && <ErrorBox message={error} />}
    </div>
  )
}
