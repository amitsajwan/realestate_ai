'use client'
import React, { useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import { compressImage } from '@/lib/app/imageCompress'
import { qualityFields } from '@/lib/app/quality'
import type { Listing } from '@/lib/app/types'
import { MAX_BROCHURE_MB, MAX_VIDEO_MB, uploadBrochure, uploadVideo } from '@/lib/app/video'
import { PhotoPicker } from './PhotoPicker'
import { Btn, ErrorBox } from './ui'

/** The run's "add them now" question, answered in place: photos, the builder's video and brochure upload right here,
 *  then the agent taps "I've added them now" and the run re-reads them. */
export function FilesUpload({ listing, onUpdated, onBusyChange }: {
  listing: Listing
  onUpdated: (l: Listing) => void
  onBusyChange?: (busy: boolean) => void
}) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [newPhotos, setNewPhotos] = useState<File[]>([])
  const videos = listing.media.filter((m) => m.kind === 'video')
  const brochures = listing.media.filter((m) => m.kind === 'document')

  async function save(ok: string, fn: () => Promise<Listing>, after?: () => void) {
    setBusy(true)
    setErr(null)
    setMsg(null)
    onBusyChange?.(true)
    try {
      onUpdated(await fn())
      setMsg(ok)
      after?.()
    } catch (e) {
      setErr(errorMessage(e))
    } finally {
      setBusy(false)
      onBusyChange?.(false)
    }
  }

  async function addPhotos() {
    await save(`${newPhotos.length} photo${newPhotos.length > 1 ? 's' : ''} added.`, async () => {
      const uploaded = await api.uploadImages(await Promise.all(newPhotos.map((f) => compressImage(f))))
      const media = [...listing.media, ...uploaded.map((u, i) => ({ url: u.url, kind: 'image' as const, order: listing.media.length + i, ...qualityFields(u) }))]
      return api.updateListing(listing.id, { media })
    }, () => setNewPhotos([]))
  }

  async function addVideo(file: File) {
    await save('Video added.', async () => {
      const up = await uploadVideo(file)
      return api.updateListing(listing.id, { media: [...listing.media, { url: up.url, kind: 'video' as const, order: listing.media.length }] })
    })
  }

  async function addBrochure(file: File) {
    await save('Brochure added.', async () => {
      const up = await uploadBrochure(file)
      return api.updateListing(listing.id, { media: [...listing.media, { url: up.url, kind: 'document' as const, order: listing.media.length }] })
    })
  }

  function remove(url: string, what: string) {
    return save(`${what} removed.`, () => api.updateListing(listing.id, { media: listing.media.filter((m) => m.url !== url) }))
  }

  return (
    <div className="space-y-3 rounded-xl border border-gray-200 bg-white p-3">
      <p className="text-sm font-semibold text-gray-800">Add them right here</p>

      <div className="space-y-2">
        <PhotoPicker files={newPhotos} onChange={setNewPhotos} />
        {newPhotos.length > 0 && <Btn disabled={busy} onClick={addPhotos}>Add {newPhotos.length} photo{newPhotos.length > 1 ? 's' : ''}</Btn>}
      </div>

      <div className="space-y-2">
        {videos.map((v) => (
          <div key={v.url} className="space-y-2">
            <video src={v.url} controls preload="metadata" playsInline className="max-h-64 rounded-lg bg-black" />
            <Btn variant="secondary" disabled={busy} onClick={() => remove(v.url, 'Video')}>Remove video</Btn>
          </div>
        ))}
        {videos.length === 0 && (
          <label className="flex min-h-[44px] cursor-pointer items-center justify-center rounded-xl border border-dashed border-gray-300 p-3 text-sm font-semibold text-blue-700">
            {busy ? 'Uploading…' : `Add a video (up to 3 minutes, ${MAX_VIDEO_MB} MB)`}
            <input type="file" accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm" className="sr-only" disabled={busy}
              onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void addVideo(f) }} />
          </label>
        )}
      </div>

      <div className="space-y-2">
        {brochures.map((b) => (
          <div key={b.url} className="flex items-center justify-between gap-2">
            <a href={b.url} target="_blank" rel="noopener noreferrer" className="flex min-h-[44px] items-center font-semibold text-blue-700 underline">Open brochure (PDF)</a>
            <Btn block={false} variant="secondary" disabled={busy} onClick={() => remove(b.url, 'Brochure')}>Remove</Btn>
          </div>
        ))}
        {brochures.length === 0 && (
          <label className="flex min-h-[44px] cursor-pointer items-center justify-center rounded-xl border border-dashed border-gray-300 p-3 text-sm font-semibold text-blue-700">
            {busy ? 'Uploading…' : `Add the brochure (PDF, up to ${MAX_BROCHURE_MB} MB)`}
            <input type="file" accept="application/pdf,.pdf" className="sr-only" disabled={busy}
              onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void addBrochure(f) }} />
          </label>
        )}
      </div>

      {msg && <p role="status" className="text-sm font-semibold text-emerald-700">{msg}</p>}
      {err && <ErrorBox message={err} />}
      <p className="text-xs text-gray-500">Then tap “I&apos;ve added them now” below, and the posts are made from them.</p>
    </div>
  )
}
