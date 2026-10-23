'use client'
import React from 'react'
import { timeAgo } from '@/lib/app/format'
import type { InboxMessage } from '@/lib/app/inbox'

const STATUS: Record<string, string> = { failed: 'Not delivered', refused: 'Not sent', dry_run: 'Test mode, not sent' }

/** One chat message: theirs on the left, ours (bot or a person) on the right. Shared by the Inbox thread and the lead page. */
export function Bubble({ m }: { m: InboxMessage }) {
  const them = m.from === 'them'
  const tone = them ? 'bg-white border border-gray-200 text-gray-900' : m.from === 'you' ? 'bg-green-100 text-green-950' : 'bg-blue-50 text-blue-950'
  const bad = m.status && STATUS[m.status]
  return (
    <li className={'flex ' + (them ? 'justify-start' : 'justify-end')}>
      <div className={'max-w-[85%] space-y-1 rounded-2xl px-3 py-2 ' + tone}>
        <p className="text-xs font-semibold opacity-70">{them ? 'They wrote' : m.from === 'you' ? 'You' : 'Bot'}{m.at ? ` · ${timeAgo(m.at)}` : ''}</p>
        <p className="whitespace-pre-wrap break-words text-sm">{m.text}</p>
        {bad && <p className="text-xs font-semibold text-red-700">{bad}{m.error ? `: ${m.error}` : ''}</p>}
      </div>
    </li>
  )
}
