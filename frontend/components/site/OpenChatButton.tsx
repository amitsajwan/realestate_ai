'use client'
import React from 'react'
import type { ChatContext } from '@/lib/site/chatContext'
import { OPEN_CHAT_EVENT } from './ChatWidget'

/** A button inside a page that opens the floating chat (ChatWidget, which every MarketingShell page has) and asks `message`.
 *  `context` names what the chat answers about when the page path does not (a project card on an area list). */
export default function OpenChatButton({ message, label, className, context }: { message: string; label: string; className?: string; context?: ChatContext }) {
  return (
    <button type="button" className={className}
      onClick={() => window.dispatchEvent(new CustomEvent(OPEN_CHAT_EVENT, { detail: { message, context } }))}>
      {label}
    </button>
  )
}
