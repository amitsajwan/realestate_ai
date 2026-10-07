'use client'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { analyzeFile } from '@/lib/app/quality'
import type { PhotoQuality } from '@/lib/app/quality'
import { t } from '@/lib/app/strings'
import { QualityBadge, QualityTip } from './quality/QualityBadge'
import { Btn } from './ui'

const MAX_PHOTOS = 10 // photos are optional and cost us storage: keep it small (backend limit is 10 too)

/** `analyze` checks each picked photo in the browser (light, blur, size) so the agent can retake a bad one; injectable for tests. */
export function PhotoPicker({ files, onChange, analyze = analyzeFile }: { files: File[]; onChange: (f: File[]) => void; analyze?: (f: File) => Promise<PhotoQuality | null> }) {
  const galleryRef = useRef<HTMLInputElement>(null)
  const cameraRef = useRef<HTMLInputElement>(null)
  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files])
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews])
  const [checks, setChecks] = useState<Map<File, PhotoQuality | null>>(() => new Map())
  useEffect(() => {
    let alive = true
    files.filter((f) => !checks.has(f)).forEach((f) => {
      analyze(f).then((q) => { if (alive) setChecks((m) => new Map(m).set(f, q)) }).catch(() => {})
    })
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files, analyze])

  const add = (list: FileList | null) => {
    if (!list) return
    const images = Array.from(list).filter((f) => f.type.startsWith('image/'))
    onChange([...files, ...images].slice(0, MAX_PHOTOS))
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <Btn variant="secondary" onClick={() => galleryRef.current?.click()}>🖼️ {t('addPhotos')}</Btn>
        <Btn variant="secondary" onClick={() => cameraRef.current?.click()}>📷 {t('takePhoto')}</Btn>
      </div>
      <input ref={galleryRef} data-testid="gallery-input" type="file" accept="image/*" multiple hidden onChange={(e) => { add(e.target.files); e.target.value = '' }} />
      <input ref={cameraRef} data-testid="camera-input" type="file" accept="image/*" capture="environment" hidden onChange={(e) => { add(e.target.files); e.target.value = '' }} />
      {files.length > 0 && (
        <ul className="grid grid-cols-3 gap-2">
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`} className="relative aspect-square overflow-hidden rounded-xl bg-gray-100">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={previews[i]} alt={f.name} className="h-full w-full object-cover" />
              <QualityBadge quality={checks.get(f)} overlay />
              <button
                type="button"
                aria-label={`Remove ${f.name}`}
                onClick={() => onChange(files.filter((_, j) => j !== i))}
                className="absolute right-1 top-1 flex h-9 w-9 items-center justify-center rounded-full bg-black/60 text-lg text-white"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      {files.some((f) => checks.get(f)?.issues.length) && (
        <div className="space-y-0.5" data-testid="photo-tips">
          {files.map((f, i) => <QualityTip key={`${f.name}-${i}`} quality={checks.get(f)} label={`Photo ${i + 1}`} />)}
        </div>
      )}
    </div>
  )
}
