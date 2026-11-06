'use client'
import Link from 'next/link'
import React, { useEffect, useRef, useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import type { ProjectHit } from '@/lib/app/types'
import { Btn, ErrorBox, inputCls } from './ui'

const WAIT_MS = 250

/**
 * The first screen of a new listing (docs/plan/listing-flow.md): most of what agents sell is a project we already have a page for, so they
 * find it by name, area or MahaRERA number and add only what is theirs. A resale or rent flat, or a project we do not hold, is described.
 */
export function ProjectPick({ title, backHref, error, onPick, onDescribe }: {
  title: string
  backHref: string
  error?: string | null
  onPick: (hit: ProjectHit) => void
  onDescribe: () => void
}) {
  const [q, setQ] = useState('')
  const [hits, setHits] = useState<ProjectHit[] | null>(null)
  const [failed, setFailed] = useState<string | null>(null)
  const asked = useRef(0)

  useEffect(() => {
    const words = q.trim()
    const mine = ++asked.current
    if (words.length < 2) {
      setHits(null)
      return
    }
    const timer = window.setTimeout(() => {
      api.searchProjects(words).then((found) => {
        if (mine === asked.current) { setHits(found); setFailed(null) }   // an older search answering late is ignored
      }).catch((e) => {
        if (mine === asked.current) setFailed(errorMessage(e))
      })
    }, WAIT_MS)
    return () => window.clearTimeout(timer)
  }, [q])

  return (
    <div className="space-y-5" data-testid="project-pick">
      <div className="flex items-center gap-2">
        <Link href={backHref} className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label="Back">←</Link>
        <h1 className="text-2xl font-bold">{title}</h1>
      </div>
      <div className="space-y-2">
        <label htmlFor="project-search" className="block font-semibold text-gray-900">Which project are you selling?</label>
        <input id="project-search" type="search" autoComplete="off" className={inputCls} value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Project name, area or MahaRERA number" />
        <p className="text-sm text-gray-600">We already have most Pune projects. Pick yours and add only your prices.</p>
      </div>
      {(failed || error) && <ErrorBox message={(error || failed) as string} />}
      {hits && hits.length > 0 && (
        <ul aria-label="Projects found" className="space-y-2">
          {hits.map((h) => (
            <li key={h.regno}>
              <button type="button" onClick={() => onPick(h)}
                className="block min-h-[56px] w-full rounded-xl border border-gray-200 bg-white p-3 text-left hover:border-[#102340]">
                <span className="block font-semibold text-gray-900">{h.marketed_name}</span>
                <span className="block text-sm text-gray-600">{[h.place_name, h.promoter].filter(Boolean).join(' · ')}</span>
                <span className="block text-xs text-gray-500">MahaRERA {h.regno}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {hits && hits.length === 0 && <p className="text-sm text-gray-700">We could not find that project. You can describe it below.</p>}
      <div className="border-t border-gray-200 pt-4">
        <Btn variant="secondary" onClick={onDescribe}>Resale or rent flat, or a project not listed here</Btn>
      </div>
    </div>
  )
}

/** The pictures the project's page already shows: ticked, so the agent starts with them and can drop any. */
export function PagePhotos({ photos, picked, onChange }: {
  photos: { url: string; alt?: string }[]
  picked: string[]
  onChange: (urls: string[]) => void
}) {
  return (
    <fieldset className="space-y-2" data-testid="page-photos">
      <legend className="font-semibold text-gray-900">Photos from the project page</legend>
      <ul className="grid grid-cols-3 gap-2">
        {photos.map((p, i) => {
          const on = picked.includes(p.url)
          return (
            <li key={p.url}>
              <label className="relative block cursor-pointer overflow-hidden rounded-lg border border-gray-200">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={p.url} alt={p.alt || `Project photo ${i + 1}`} loading="lazy" style={{ aspectRatio: '1 / 1', objectFit: 'cover' }} className={`block w-full ${on ? '' : 'opacity-40'}`} />
                <input type="checkbox" className="absolute left-1 top-1 h-5 w-5" checked={on} aria-label={`Use photo ${i + 1}`}
                  onChange={(e) => onChange(e.target.checked ? [...picked, p.url] : picked.filter((u) => u !== p.url))} />
              </label>
            </li>
          )
        })}
      </ul>
    </fieldset>
  )
}
