'use client'

import React, { useState } from 'react'

/** Copies the finder's address (the choices made) for pasting anywhere; says "Copied" for a moment. */
export default function CopyLink({ url, className = '' }: { url: string; className?: string }) {
  const [done, setDone] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setDone(true)
      setTimeout(() => setDone(false), 2500)
    } catch {
      window.prompt?.('Copy this link', url)
    }
  }
  return (
    <button type="button" onClick={copy} className={className} data-testid="finder-copy">
      {done ? '✓ Link copied' : 'Copy link'}
    </button>
  )
}
