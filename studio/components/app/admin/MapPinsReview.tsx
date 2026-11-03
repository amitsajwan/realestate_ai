'use client'
import React, { useEffect, useState } from 'react'
import { adminApi, type MapPinWaiting } from '@/lib/app/admin'
import { errorMessage } from '@/lib/app/client'
import { useAsync } from '@/lib/app/useAsync'
import { Btn, ErrorBox, Spinner } from '../ui'

/** Studio > Admin > Map pins to check (backend areastats/mappins.py): places Google gave for a project's sold-under name that
 *  only partly matched. Yes puts the pin on the area map at once; No never offers that place again for the project, and the next
 *  daily round looks for another. Open the place on Google Maps before answering. */
export function MapPinsReview() {
  const { data, error, loading } = useAsync(() => adminApi.mapPins(), [])
  const [items, setItems] = useState<MapPinWaiting[]>([])
  const [busy, setBusy] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  useEffect(() => { if (data) setItems(data) }, [data])

  async function decide(regno: string, approve: boolean) {
    setBusy(regno)
    setSaveError(null)
    try {
      setItems(await adminApi.decideMapPin(regno, approve))
    } catch (e) {
      setSaveError(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <Spinner />
  if (error) return <ErrorBox message={errorMessage(error)} />
  return (
    <div data-testid="map-pins">
      <p className="text-sm text-gray-600">
        The area maps place a project only where we are sure. These places only partly matched the name the project is sold
        under: open each on Google Maps, then say whether it is the project&apos;s site.
      </p>
      {saveError && <div className="mt-2"><ErrorBox message={saveError} /></div>}
      {!items.length ? (
        <p className="mt-3 rounded-xl bg-gray-50 px-3 py-2 text-sm text-gray-600" data-testid="map-pins-empty">Nothing to check.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {items.map((p) => (
            <li key={p.regno} className="rounded-xl border border-gray-200 bg-white p-3" data-testid="map-pin">
              <p className="font-semibold text-gray-900">{p.project}{p.area ? <span className="font-normal text-gray-500"> · {p.area}</span> : null}</p>
              <p className="text-xs text-gray-500">{[p.registered_name !== p.project ? p.registered_name : null, p.regno, p.promoter].filter(Boolean).join(' · ')}</p>
              <p className="mt-2 text-sm text-gray-800">Google&apos;s place: <span className="font-semibold">{p.google_name}</span></p>
              {p.address && <p className="text-sm text-gray-600">{p.address}</p>}
              {p.sold_as && <p className="mt-1 text-xs text-gray-500">Searched as &ldquo;{p.sold_as}&rdquo;</p>}
              <a href={p.maps_url} target="_blank" rel="noopener noreferrer"
                className="mt-2 inline-flex min-h-[44px] items-center text-sm font-semibold text-blue-700 underline underline-offset-2">See it on Google Maps</a>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <Btn onClick={() => decide(p.regno, true)} disabled={busy === p.regno} data-testid="map-pin-yes">Yes, that is the site</Btn>
                <Btn variant="secondary" onClick={() => decide(p.regno, false)} disabled={busy === p.regno} data-testid="map-pin-no">No</Btn>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
