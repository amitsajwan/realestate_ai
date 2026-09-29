'use client'
import React, { useEffect, useMemo, useRef } from 'react'
import { t } from '@/lib/app/strings'
import { Btn } from './ui'

const MAX_PHOTOS = 20 // backend limit (MAX_IMAGES_PER_PROPERTY)

export function PhotoPicker({ files, onChange }: { files: File[]; onChange: (f: File[]) => void }) {
  const galleryRef = useRef<HTMLInputElement>(null)
  const cameraRef = useRef<HTMLInputElement>(null)
  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files])
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews])

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
    </div>
  )
}
