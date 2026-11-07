'use client'
import React, { useEffect, useState } from 'react'
import { Btn, ErrorBox, Spinner } from '@/components/app/ui'
import { brochureApi, pendingFacts } from '@/lib/app/brochure'
import type { BrochureApi, BrochureFact, BrochureImage, BrochureReading } from '@/lib/app/brochure'
import { useBrochure } from '@/lib/app/useBrochure'

/** "We read your brochure": each PDF is read once, in the background (docs/plan/brochure-reading.md). Plans go on the project
 *  page unless the agent removes them; a fact waits for the agent's tick; posts use only the pictures the agent picks. */
const POLL_MS = 8000
const KIND: Record<BrochureImage['kind'], string> = {
  floor_plan: 'Floor plan', master_plan: 'Master plan', location_map: 'Location map', render: "Artist's impression",
}

function PlanCard({ listingId, image, client, busy, onSet }: {
  listingId: string
  image: BrochureImage
  client: BrochureApi
  busy: boolean
  onSet: (state: BrochureImage['state']) => void
}) {
  const [src, setSrc] = useState<string | null>(null)
  useEffect(() => {
    let live = true
    client.image(listingId, image.id).then((u) => { if (live) setSrc(u) }).catch(() => undefined)
    return () => { live = false }
  }, [client, listingId, image.id])
  const dropped = image.state === 'dropped'
  return (
    <li className={`space-y-2 rounded-xl border border-gray-200 p-2 ${dropped ? 'opacity-60' : ''}`}>
      {src ? <img src={src} alt={`${KIND[image.kind]}, page ${image.page}`} className="w-full rounded-lg bg-gray-50" /> : <div className="h-32 rounded-lg bg-gray-100" />}
      <p className="text-sm font-semibold">{KIND[image.kind]} <span className="font-normal text-gray-600">· page {image.page}</span></p>
      <p className="text-xs text-gray-600">
        {dropped ? 'Removed. Not on the project page or in posts.' : image.state === 'confirmed' ? 'On the project page and used in posts.' : 'On the project page. Not in posts yet.'}
      </p>
      <div className="flex gap-2">
        {image.state !== 'confirmed' && <Btn block={false} variant="secondary" disabled={busy} onClick={() => onSet('confirmed')}>Use in posts</Btn>}
        {dropped
          ? <Btn block={false} variant="secondary" disabled={busy} onClick={() => onSet('pending')}>Put back</Btn>
          : <Btn block={false} variant="secondary" disabled={busy} onClick={() => onSet('dropped')}>Remove</Btn>}
      </div>
    </li>
  )
}

function factText(f: BrochureFact): string {
  const v = Array.isArray(f.value) ? f.value.join(', ') : String(f.value)
  return f.key === 'carpet_area' && f.config ? `${f.config}: ${v}` : v
}

export function BrochureCheck({ listingId, client = brochureApi, pollMs = POLL_MS }: { listingId: string; client?: BrochureApi; pollMs?: number }) {
  const b = useBrochure(listingId, client)
  const { reload } = b
  const [reading, setReading] = useState<BrochureReading | null>(null)

  useEffect(() => {
    let live = true
    let timer: ReturnType<typeof setTimeout> | undefined
    const look = async () => {
      try {
        const r = await client.reading(listingId)
        if (!live) return
        setReading((was) => {
          if (r.status === 'done' && was && was.status !== 'done') void reload()
          return r
        })
        if (r.status === 'queued' || r.status === 'reading') timer = setTimeout(() => void look(), pollMs)
      } catch {
        // the status line is a nicety: the kit below still loads
      }
    }
    void look()
    return () => {
      live = false
      if (timer) clearTimeout(timer)
    }
  }, [client, listingId, pollMs, reload])

  const waiting = reading?.status === 'queued' || reading?.status === 'reading'
  const kit = b.kit
  if (waiting) {
    return <p role="status" className="rounded-lg bg-blue-50 p-3 text-sm text-blue-900">We&apos;re reading your brochure. This takes a minute or two, and you can leave this page.</p>
  }
  if (b.loading) return <Spinner />
  if (!kit) {
    return reading?.status === 'failed' ? <p role="status" className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">{reading.note}</p> : null
  }
  const images = kit.images ?? []
  const held = kit.registration.status !== 'verified'
  const pending = pendingFacts(kit)
  return (
    <div className="space-y-3" aria-label="What we read from your brochure">
      <p className="font-semibold">What we read from your brochure</p>
      {held
        ? <p role="alert" className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">{kit.registration.note} Nothing from it goes on the project page until this is sorted out.</p>
        : <p className="text-sm text-gray-600">MahaRERA {kit.registration.rera_no} matches this project. Plans go on the project page, and buyers see them after the form. Remove any that are wrong.</p>}
      {b.error && <ErrorBox message={b.error} />}
      {images.length > 0 && (
        <ul className="grid gap-2 sm:grid-cols-2">
          {images.map((im) => (
            <PlanCard key={im.id} listingId={listingId} image={im} client={client} busy={!!b.saving[`img:${im.id}`]} onSet={(s) => void b.setImage(im.id, s)} />
          ))}
        </ul>
      )}
      {kit.facts.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-gray-800">Details. Tick the ones that are right, and only those are used.</p>
          <ul className="space-y-2">
            {kit.facts.map((f) => (
              <li key={f.id} className={`rounded-xl border border-gray-200 p-3 text-sm ${f.state === 'dropped' ? 'opacity-60' : ''}`}>
                <p className="font-semibold">{f.label} <span className="font-normal text-gray-600">· page {f.page}</span></p>
                <p className="text-gray-800">{factText(f)}</p>
                <div className="mt-2 flex gap-2">
                  {f.state !== 'confirmed' && <Btn block={false} variant="secondary" disabled={!!b.saving[f.id]} onClick={() => void b.setFact(f.id, 'confirmed')}>Right</Btn>}
                  {f.state !== 'dropped' && <Btn block={false} variant="secondary" disabled={!!b.saving[f.id]} onClick={() => void b.setFact(f.id, 'dropped')}>Wrong</Btn>}
                  {f.state === 'confirmed' && <span className="self-center font-semibold text-green-700">Ticked</span>}
                </div>
              </li>
            ))}
          </ul>
          {pending.length > 1 && <Btn variant="secondary" onClick={() => void b.confirmAll()}>All {pending.length} are right</Btn>}
        </div>
      )}
    </div>
  )
}
