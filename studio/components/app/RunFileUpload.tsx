'use client'
import React, { useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import { MAX_BROCHURE_MB, MAX_VIDEO_MB, uploadBrochure, uploadVideo } from '@/lib/app/video'

type Kind = 'document' | 'video'

/** Inline brochure / video upload for the run's 'files' question: uploads, attaches it to the listing's media (as the
 *  listing's Files tab does), then calls `onAdded` so the run carries on. */
export function RunFileUpload({ listingId, onAdded }: { listingId: string; onAdded: () => Promise<void> }) {
  const [busy, setBusy] = useState<Kind | null>(null)
  const [error, setError] = useState<string | null>(null)

  const add = async (kind: Kind, file: File) => {
    setBusy(kind)
    setError(null)
    try {
      const up = kind === 'video' ? await uploadVideo(file) : await uploadBrochure(file)
      const listing = await api.getListing(listingId)
      await api.updateListing(listingId, { media: [...listing.media, { url: up.url, kind, order: listing.media.length }] })
      await onAdded()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  const input = (kind: Kind, label: string, accept: string, max: number) => (
    <label className={`flex min-h-[44px] cursor-pointer items-center rounded-full border border-blue-600 bg-white px-4 text-sm font-semibold text-blue-700 ${busy ? 'opacity-50' : ''}`}>
      {busy === kind ? 'Uploading…' : label}
      <input type="file" accept={accept} className="sr-only" disabled={busy !== null} aria-label={`${label} (up to ${max} MB)`}
        onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void add(kind, f) }} />
    </label>
  )

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {input('document', 'Add brochure (PDF)', 'application/pdf', MAX_BROCHURE_MB)}
        {input('video', 'Add video', 'video/*', MAX_VIDEO_MB)}
      </div>
      {busy && <p role="status" className="text-sm text-gray-700">Uploading, keep this page open…</p>}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
    </div>
  )
}
