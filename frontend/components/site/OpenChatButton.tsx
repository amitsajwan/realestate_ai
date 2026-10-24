'use client'
import React from 'react'
import { OPEN_CHAT_EVENT } from './ChatWidget'

/** A button inside a page that opens the floating chat (ChatWidget, which every MarketingShell page has) and asks `message`. */
export default function OpenChatButton({ message, label, className }: { message: string; label: string; className?: string }) {
  return (
    <button type="button" className={className}
      onClick={() => window.dispatchEvent(new CustomEvent(OPEN_CHAT_EVENT, { detail: { message } }))}>
      {label}
    </button>
  )
}
