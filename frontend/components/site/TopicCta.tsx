'use client'
import React from 'react'
import { openChat } from '@/lib/site/chatApi'

/** A guide's call to action: one line of copy and a button that opens the floating chat with the visitor's question already asked. */
export default function TopicCta({ text, button, message }: { text: string; button: string; message: string }) {
  return (
    <aside data-print="hide" className="mt-6 flex flex-col gap-3 rounded-xl border border-[#0f2340] bg-[#0f2340] p-4 text-white sm:flex-row sm:items-center sm:justify-between">
      <p className="font-semibold">{text}</p>
      <button type="button" onClick={() => openChat(message)}
        className="min-h-[44px] shrink-0 rounded-lg bg-[#f0b440] px-4 font-bold text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-white">
        {button}
      </button>
    </aside>
  )
}
