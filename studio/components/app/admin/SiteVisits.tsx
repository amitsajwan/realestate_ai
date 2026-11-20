'use client'
import React, { useEffect, useState } from 'react'
import { adminApi, type SiteVisit } from '@/lib/app/admin'
import { errorMessage } from '@/lib/app/client'
import { useAsync } from '@/lib/app/useAsync'
import { Btn, ErrorBox, Field, Spinner, inputCls } from '../ui'

const today = () => new Date().toISOString().slice(0, 10)
const words = (s: string) => (s.trim() ? s.trim().split(/\s+/).length : 0)

/** Studio > Site > On the ground (backend areastats/sitevisits.py): a note from someone who went to a project's site, shown on its
 *  page as "Visited <day> by <who>". The one part of a project page no program can make, so it is written by the person who went
 *  and never by a model. The server checks it (60 to 250 words, no phone, link, hype or price talk) and says what to change. */
export function SiteVisits() {
  const { data, error, loading } = useAsync(() => adminApi.siteVisits(), [])
  const [items, setItems] = useState<SiteVisit[]>([])
  const [project, setProject] = useState('')
  const [day, setDay] = useState(today())
  const [by, setBy] = useState('')
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  useEffect(() => { if (data) setItems(data) }, [data])

  async function save() {
    setBusy(true)
    setSaveError(null)
    setSaved(false)
    try {
      setItems(await adminApi.addSiteVisit({ project: project.trim(), visited_on: day, by: by.trim() || undefined, text }))
      setText('')
      setSaved(true)
    } catch (e) {
      setSaveError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function withdraw(v: SiteVisit) {
    if (!v.at) return
    setSaveError(null)
    try {
      setItems(await adminApi.withdrawSiteVisit(v.regno, v.at))
    } catch (e) {
      setSaveError(errorMessage(e))
    }
  }

  if (loading) return <Spinner />
  if (error) return <ErrorBox message={errorMessage(error)} />
  const n = words(text)
  return (
    <div className="space-y-4" data-testid="site-visits">
      <p className="text-sm text-gray-600">
        After a site visit, write what you saw: the approach road, how far the building has got, how close the towers stand, the
        traffic at the gate. It goes on the project&apos;s page with the day and who went. Facts only; no prices, phone numbers or
        praise.
      </p>
      <div className="space-y-2 rounded-2xl bg-white p-3">
        <Field label="Project: page address or MahaRERA number" htmlFor="visit-project">
          <input id="visit-project" className={inputCls} value={project} onChange={(e) => setProject(e.target.value)}
            placeholder="avasetu.in/projects/godrej-ivara-pune" />
        </Field>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Visited on" htmlFor="visit-day">
            <input id="visit-day" type="date" className={inputCls} value={day} max={today()} onChange={(e) => setDay(e.target.value)} />
          </Field>
          <Field label="Who went" htmlFor="visit-by">
            <input id="visit-by" className={inputCls} value={by} onChange={(e) => setBy(e.target.value)} placeholder="House Deal" maxLength={60} />
          </Field>
        </div>
        <Field label={`What you saw (${n} words; 60 to 250)`} htmlFor="visit-text">
          <textarea id="visit-text" className={`${inputCls} min-h-[180px] py-3`} value={text} onChange={(e) => setText(e.target.value)} />
        </Field>
        {saveError && <ErrorBox message={saveError} />}
        {saved && <p className="text-sm font-semibold text-green-700" data-testid="visit-saved">Saved. The page shows it within a few minutes.</p>}
        <Btn onClick={save} disabled={busy || !project.trim() || n < 1} data-testid="visit-save">{busy ? 'Saving...' : 'Put it on the page'}</Btn>
      </div>
      {items.length > 0 && (
        <ul className="space-y-2" data-testid="visit-list">
          {items.map((v) => (
            <li key={`${v.regno}-${v.at}`} className={`rounded-xl border border-gray-200 bg-white p-3 ${v.withdrawn ? 'opacity-60' : ''}`} data-testid="visit">
              <p className="font-semibold text-gray-900">{v.project ?? v.regno}</p>
              <p className="text-xs text-gray-500">Visited {v.visited_on} by {v.by}{v.withdrawn ? ' · taken off the page' : ''}</p>
              <p className="mt-1 text-sm text-gray-800">{v.text}</p>
              {!v.withdrawn && (
                <button type="button" onClick={() => withdraw(v)} className="mt-1 min-h-[44px] text-sm font-semibold text-red-700 underline underline-offset-2"
                  data-testid="visit-withdraw">Take off the page</button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
