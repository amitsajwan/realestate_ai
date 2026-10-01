'use client'
import React from 'react'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { ChatConversation, FacebookInterest, FacebookStatus } from '@/lib/app/types'
import { getNotifications, getWhatsAppConversations, markNotificationRead, REPLY_STATUS_LABEL, type WhatsAppConversation } from '@/lib/app/whatsapp'

const CHIP: Record<string, string> = {
  interested: 'bg-green-100 text-green-800',
  question: 'bg-blue-100 text-blue-800',
  praise: 'bg-pink-100 text-pink-800',
  complaint: 'bg-red-100 text-red-800',
  other: 'bg-gray-100 text-gray-700',
}

function Row({ c }: { c: FacebookInterest }) {
  const ig = c.channel === 'instagram'
  return (
    <li className={'space-y-2 rounded-2xl border bg-white p-4 ' + (c.needs_human ? 'border-amber-400' : 'border-gray-200')}>
      <div className="flex items-center justify-between gap-2">
        <p className="font-semibold">{c.from_name || 'Someone'}{ig && <span className="ml-2 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-semibold text-purple-800">Instagram</span>}</p>
        <span className={'rounded-full px-2.5 py-0.5 text-xs font-semibold ' + (CHIP[c.intent] ?? CHIP.other)}>{c.intent}</span>
      </div>
      <p className="text-gray-800">&ldquo;{c.text}&rdquo;</p>
      {c.needs_human && <p role="note" className="rounded-lg bg-amber-50 p-2 text-sm font-semibold text-amber-900">Needs you: {c.reason || 'please answer this one'}</p>}
      {c.reply && (
        <p className="rounded-lg bg-gray-50 p-2 text-sm text-gray-700">
          <span className="font-semibold">{c.status === 'replied' ? 'We replied: ' : c.status === 'dry_run' ? 'Would reply (test mode): ' : 'Draft reply: '}</span>{c.reply}
        </p>
      )}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>{c.created_time ? timeAgo(c.created_time) : ''}</span>
        {c.permalink && <a href={c.permalink} target="_blank" rel="noopener noreferrer" className="flex min-h-[44px] items-center font-semibold text-blue-700 underline">{ig ? 'Open on Instagram' : 'Open on Facebook'}</a>}
      </div>
    </li>
  )
}

function WhatsAppChats({ chats }: { chats: WhatsAppConversation[] }) {
  const needs = chats.filter((c) => c.needs_human && !c.opted_out).length
  return (
    <section aria-label="WhatsApp chats" className="space-y-2">
      <h2 className="text-lg font-bold">WhatsApp chats{needs > 0 && <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-sm text-amber-900">{needs} need you</span>}</h2>
      <ul className="space-y-3">
        {chats.map((c) => (
          <li key={c.id} className={'space-y-2 rounded-2xl border bg-white p-4 ' + (c.needs_human ? 'border-amber-400' : 'border-gray-200')}>
            <div className="flex items-center justify-between gap-2">
              <p className="font-semibold">
                {c.name || 'WhatsApp buyer'}
                <span className="ml-2 rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800">WhatsApp</span>
              </p>
              <span className="text-sm text-gray-500">{c.updated_at ? timeAgo(c.updated_at) : ''}</span>
            </div>
            <p className="text-sm text-gray-700">{c.summary}</p>
            {c.interest_title && <p className="text-sm text-gray-600">About: {c.interest_title}</p>}
            {c.opted_out && <p className="text-sm font-semibold text-red-800">They replied STOP: do not message them on WhatsApp.</p>}
            {c.needs_human && !c.opted_out && <p className="text-sm font-semibold text-amber-900">They asked something we could not answer. Please reply to them yourself.</p>}
            <ol className="space-y-1">
              {c.messages.map((m, i) => (
                <li key={i} className={'rounded-lg p-2 text-sm ' + (m.role === 'user' ? 'bg-gray-50 text-gray-900' : 'bg-green-50 text-gray-700')}>
                  <span className="font-semibold">{m.role === 'user' ? 'Buyer: ' : 'Assistant: '}</span>
                  {m.text}
                  {m.role === 'bot' && m.status && m.status !== 'sent' && <span className="ml-1 text-xs text-gray-500">({REPLY_STATUS_LABEL[m.status] ?? m.status})</span>}
                </li>
              ))}
            </ol>
            <p className="text-xs text-gray-500">{c.phone}{c.lead_id ? ' · saved in Leads' : ''}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function InterestPage() {
  const { data, error, loading } = useAsync(async () => ({
    comments: await api.getFacebookInterest(),
    chats: await api.getChatConversations().catch(() => [] as ChatConversation[]),
    fb: await api.getFacebookStatus().catch(() => null as FacebookStatus | null),
    whatsapp: await getWhatsAppConversations().catch(() => [] as WhatsAppConversation[]),
  }), [])
  const waCount = data?.whatsapp?.length ?? 0
  React.useEffect(() => {
    // seeing the WhatsApp chats here clears the WhatsApp badge on the Studio home
    if (!waCount) return
    getNotifications(true)
      .then((n) => Promise.all(n.items.filter((x) => x.kind.includes('whatsapp')).map((x) => markNotificationRead(x.id))))
      .catch(() => undefined)
  }, [waCount])
  if (loading && !data) return <Spinner />
  if (error) return <ErrorBox message={error} />
  const items = data?.comments ?? []
  const chats = data?.chats ?? []
  const needs = items.filter((c) => c.needs_human)
  const chatsNeedingYou = chats.filter((c) => c.needs_human)
  const whatsapp = data?.whatsapp ?? []
  return (
    <div className="space-y-4">
      <PageTitle>{t('interest')}</PageTitle>
      {(data?.fb?.reconnect || data?.fb?.instagram?.reconnect) && (
        <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-800">The Facebook connection has stopped working, so comments are not being answered right now. Ask your PUNE Property admin to reconnect it.</p>
      )}
      <p className="text-sm text-gray-600">People who commented on your posts on the PUNE Property Page and Instagram. Interested people are answered automatically; questions we cannot answer wait here for you.</p>
      {whatsapp.length > 0 && <WhatsAppChats chats={whatsapp} />}
      {chats.length > 0 && (
        <section aria-label="Website chats" className="space-y-2">
          <h2 className="text-lg font-bold">Website chats{chatsNeedingYou.length > 0 && <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-sm text-amber-900">{chatsNeedingYou.length} need you</span>}</h2>
          <ul className="space-y-3">
            {chats.map((c) => (
              <li key={c.id} className={'space-y-1 rounded-2xl border bg-white p-4 ' + (c.needs_human ? 'border-amber-400' : 'border-gray-200')}>
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold">{c.name || 'Website visitor'}</p>
                  <span className={'rounded-full px-2.5 py-0.5 text-xs font-semibold ' + (c.lead_created ? 'bg-green-100 text-green-800' : c.needs_human ? 'bg-amber-100 text-amber-900' : 'bg-gray-100 text-gray-700')}>
                    {c.lead_created ? 'lead saved' : c.needs_human ? 'needs you' : 'chatting'}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{c.summary}</p>
                {c.questions.length > 0 && <p className="text-sm text-gray-600">Asked: {c.questions.map((q) => `"${q}"`).join(' · ')}</p>}
                {c.needs_human && <p className="text-sm font-semibold text-amber-900">They asked something we could not answer and have not left a number. If they come back and share it, it will appear in Leads.</p>}
              </li>
            ))}
          </ul>
        </section>
      )}
      {items.length === 0 ? (
        <p className="rounded-2xl bg-white p-6 text-center text-gray-600">No comments yet. When someone comments INTERESTED on a post, they show up here.</p>
      ) : (
        <>
          {needs.length > 0 && <p className="rounded-xl bg-amber-50 p-3 text-sm font-semibold text-amber-900">{needs.length} need{needs.length === 1 ? 's' : ''} you</p>}
          <ul className="space-y-3">{items.map((c) => <Row key={c.id} c={c} />)}</ul>
        </>
      )}
    </div>
  )
}
